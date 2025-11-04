import argparse
import datetime
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from jira import JIRA, Issue
from tqdm import tqdm

DEV_MODE = os.getenv("DEV_MODE") == "true"
dotenv_path = os.path.expanduser("~/.jira_changelog_generator") if not DEV_MODE else ".env"
load_dotenv(dotenv_path=dotenv_path)

jira_client = JIRA(os.getenv("JIRA_HOST"),
                   basic_auth=(os.getenv("JIRA_USERNAME"), os.getenv("JIRA_API_TOKEN")))


def get_epic(issue: Issue) -> Issue | None:
    if not hasattr(issue.fields, "parent"):
        return None

    parent: Issue = issue.fields.parent

    if parent.fields.issuetype.name == "Story":
        story = jira_client.search_issues(f"key = {parent.key}")[0]
        parent = jira_client.search_issues(f"key = {story.fields.parent.key}")[0]

    return parent


def generate_report(df: pd.DataFrame) -> str:
    content = f"# ISSUES IN TEST ENVIRONMENT DATE: {datetime.date.today().strftime("%d/%m/%Y")}\n"

    for application in df["issue_labels"].sort_values(na_position='last').explode().unique():
        if application:
            content += f"## {application}\n"
            df_application: pd.DataFrame = df[df["issue_labels"].apply(lambda i: i is not None and application in i)]
        else:
            content += "## Application Unknown\n"
            df_application: pd.DataFrame = df[df["issue_labels"].isna()]

        df_epic = df_application[["epic_key", "epic_name"]].drop_duplicates().sort_values("epic_key",
                                                                                          na_position='last')
        for _, epic_key, epic_name in df_epic.itertuples():
            if epic_key:
                content += f"### [{epic_key}]({os.getenv("JIRA_HOST")}/browse/{epic_key}) {epic_name}\n"
                df_issue: pd.DataFrame = df_application[df_application["epic_key"] == epic_key]
            else:
                content += "### Epic Unknown\n"
                df_issue: pd.DataFrame = df_application[df_application["epic_key"].isna()]

            df_features: pd.DataFrame = df_issue[(df_issue["issue_type"] == "Sviluppo")][["issue_key", "issue_name"]]
            if not df_features.empty:
                content += "**Features:**\n"
                for _, issue_key, issue_name in df_features.itertuples():
                    content += f"- [{issue_key}]({os.getenv("JIRA_HOST")}/browse/{issue_key}) {issue_name}\n"

            df_bugfixes: pd.DataFrame = df_issue[(df_issue["issue_type"] == "Bug")][["issue_key", "issue_name"]]
            if not df_bugfixes.empty:
                content += "**Bugfixes:**\n"
                for _, issue_key, issue_name in df_bugfixes.itertuples():
                    content += f"- [{issue_key}]({os.getenv("JIRA_HOST")}/browse/{issue_key}) {issue_name}\n"

    return content


def main(date: datetime.date):
    days_difference = (datetime.date.today() - date).days if date else 30
    jira_updated = f"-{days_difference}d"

    df = pd.DataFrame(
        columns=["issue_key", "issue_name", "issue_description", "issue_type", "issue_labels", "epic_key",
                 "epic_name", "epic_type"])
    issues = jira_client.search_issues(
        f"project IN ({os.getenv("JIRA_PROJECT")}) AND status = {os.getenv("JIRA_STATUS")} AND type IN (Sviluppo,Bug) AND updated >= {jira_updated}",
        maxResults=0)

    print(
        f"find {len(issues)} issues in the {os.getenv("JIRA_STATUS")} status of the {os.getenv('JIRA_PROJECT')} project from last {days_difference} days")
    print("processing issues...")

    for issue in tqdm(issues):
        epic = get_epic(issue)
        df.loc[df.size + 1] = [issue.key, issue.fields.summary, issue.fields.description, issue.fields.issuetype.name,
                               issue.fields.labels or None, epic.key if epic else None,
                               epic.fields.summary if epic else None,
                               epic.fields.issuetype.name if epic else None]

    print("generating report...")
    with open("report.md", "w") as f:
        f.write(generate_report(df))
    print(f"writing report to file {os.getcwd()}/report.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate JIRA changelog report')
    parser.add_argument('--date', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(),
                        help='Start date for report generation (YYYY-MM-DD format)')
    args = parser.parse_args()
    try:
        main(args.date)
    except KeyboardInterrupt:
        sys.exit(0)
