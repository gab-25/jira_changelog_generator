# jira_changelog_generator

This script generates a Markdown report (`report.md`) based on issues from a Jira project. The report groups issues by
application (using Jira labels) and by epic, separating new features from bug fixes.

## Prerequisites

- Python 3.x
- The dependencies listed in the `requirements.txt` file.

## Installation

1. Clone this repository to your computer.
2. Install the necessary dependencies by running the following command from the project root:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Before running the script, you need to configure your Jira credentials and project specifications.

Create a configuration file. The script looks for the file in two locations:

1. **Development Mode**: A `.env` file in the project's root directory. To enable this mode, set the `DEV_MODE`
   environment variable to `"true"`.
2. **Normal Mode**: A file named `.jira_changelog_generator` in your home directory (`~/.jira_changelog_generator`).

The configuration file must contain the following variables:

- `JIRA_HOST`: The URL of your Jira instance.
- `JIRA_USERNAME`: Your username for Jira access (usually your email).
- `JIRA_API_TOKEN`: An API token generated from Jira for authentication. You can create one by following
  the [official Atlassian guide](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/).
- `JIRA_PROJECT`: The key of the Jira project from which you want to extract issues (e.g., "PROJ").
- `JIRA_STATUS`: The status of the issues you want to include in the report (e.g., "In Test", "Done", "Completed").

## Usage

Once the configuration is complete, run the script with the following command:

```bash
python main.py
```

The script will connect to Jira, retrieve the issues that match the defined criteria (`project`, `status`, and type
`Sviluppo` or `Bug`), and generate a `report.md` file in the project's root directory.

The report will be formatted as follows:

- A title with the generation date.
- A section for each "application" (based on issue labels).
- A sub-section for each "epic".
- Bulleted lists for "Features" (issues of type "Sviluppo") and "Bugfixes" (issues of type "Bug").