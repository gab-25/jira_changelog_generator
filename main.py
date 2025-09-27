import datetime
import os

import pandas as pd
from dotenv import load_dotenv
from jira import JIRA, Issue

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

    applications = filter(lambda i: i in os.getenv("JIRA_ISSUE_LABELS").split(","),
                          df["issue_labels"].explode().unique().tolist())
    for application in applications:
        content += f"## {application}\n"

        df_epic: pd.DataFrame = df[df["issue_labels"].apply(lambda i: application in i)][
            ["epic_key", "epic_name"]].drop_duplicates().sort_values("epic_key", na_position='last')
        for _, epic_key, epic_name in df_epic.itertuples():
            if epic_key:
                content += f"### [{epic_key}]({os.getenv("JIRA_HOST")}/browse/{epic_key}) {epic_name}\n"
            else:
                content += "### Epic Unknown\n"

            df_features: pd.DataFrame = df[(df["epic_key"] == epic_key) & (df["issue_type"] == "Sviluppo")][
                ["issue_key", "issue_name"]]
            if not df_features.empty:
                content += "**Features:**\n"
                for _, issue_key, issue_name in df_features.itertuples():
                    content += f"- [{issue_key}]({os.getenv("JIRA_HOST")}/browse/{issue_key}) {issue_name}\n"

            if epic_key:
                df_bugfixes = df[(df["epic_key"] == epic_key)]
            else:
                df_bugfixes = df[(df["epic_key"].isna())]
            df_bugfixes = df_bugfixes[
                (df_bugfixes["issue_type"] == "Bug") & df_bugfixes["issue_labels"].apply(lambda i: application in i)][
                ["issue_key", "issue_name"]]
            if not df_bugfixes.empty:
                content += "**Bugfixes:**\n"
                for _, issue_key, issue_name in df_bugfixes.itertuples():
                    content += f"- [{issue_key}]({os.getenv("JIRA_HOST")}/browse/{issue_key}) {issue_name}\n"

    return content


def main():
    df = pd.DataFrame(
        columns=["issue_key", "issue_name", "issue_description", "issue_type", "issue_labels", "epic_key",
                 "epic_name", "epic_type"])
    issues = jira_client.search_issues(
        f"project = {os.getenv("JIRA_PROJECT")} AND status = {os.getenv("JIRA_STATUS")} AND type IN ({os.getenv("JIRA_ISSUE_TYPES")}) AND labels IN ({os.getenv("JIRA_ISSUE_LABELS")})",
        maxResults=0)

    print(f"find {len(issues)} issues in {os.getenv("JIRA_STATUS")} status")

    for issue in issues:
        print(f"processing issue {issue.key}")

        epic = get_epic(issue)
        df.loc[df.size + 1] = [issue.key, issue.fields.summary, issue.fields.description, issue.fields.issuetype.name,
                               issue.fields.labels, epic.key if epic else None, epic.fields.summary if epic else None,
                               epic.fields.issuetype.name if epic else None]

    print(f"writing report to file {os.getcwd()}/report.md")
    with open("report.md", "w") as f:
        f.write(generate_report(df))


if __name__ == "__main__":
    main()
