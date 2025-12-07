"""
GitHub API client for PR management

Provides:
- Create pull requests
- Link to issues
- Add review checklists
- Set labels and reviewers
- Comment on PRs
"""

import os
import requests
from typing import List, Optional, Dict
from dataclasses import dataclass

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class GitHubError(ForgeError):
    """GitHub API errors"""
    pass


@dataclass
class PullRequest:
    """Pull request information"""
    number: int
    title: str
    url: str
    html_url: str
    state: str
    head: str
    base: str


@dataclass
class Issue:
    """GitHub issue information"""
    number: int
    title: str
    state: str
    labels: List[str]


class GitHubClient:
    """
    GitHub API client.

    Features:
    - Create PRs with comprehensive descriptions
    - Link to issues
    - Add review checklists
    - Set labels and reviewers
    - Comment on PRs
    """

    def __init__(
        self,
        repo: str,
        token: Optional[str] = None,
        api_url: str = "https://api.github.com"
    ):
        """
        Initialize GitHub client.

        Args:
            repo: Repository in format "owner/repo"
            token: GitHub personal access token
            api_url: GitHub API URL
        """
        if "/" not in repo:
            raise GitHubError(f"Invalid repo format: {repo}. Expected 'owner/repo'")

        self.owner, self.repo_name = repo.split("/", 1)
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.api_url = api_url.rstrip("/")

        if not self.token:
            raise GitHubError(
                "GitHub token required. Set GITHUB_TOKEN environment variable "
                "or pass token parameter"
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        })

        logger.info(f"Initialized GitHub client for {self.repo}")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make GitHub API request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body
            params: Query parameters

        Returns:
            Response data

        Raises:
            GitHubError: If request fails
        """
        url = f"{self.api_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            )

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.HTTPError as e:
            error_msg = f"GitHub API error: {e.response.status_code}"
            if e.response.content:
                try:
                    error_data = e.response.json()
                    error_msg += f" - {error_data.get('message', '')}"
                except:
                    pass

            logger.error(error_msg)
            raise GitHubError(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub request failed: {e}")
            raise GitHubError(f"GitHub request failed: {e}")

    def create_pr(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        draft: bool = False,
        maintainer_can_modify: bool = True
    ) -> PullRequest:
        """
        Create pull request.

        Args:
            title: PR title
            body: PR description
            head: Source branch
            base: Target branch
            draft: Create as draft PR
            maintainer_can_modify: Allow maintainer edits

        Returns:
            PullRequest object
        """
        endpoint = f"/repos/{self.repo}/pulls"

        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "draft": draft,
            "maintainer_can_modify": maintainer_can_modify
        }

        result = self._request("POST", endpoint, data=data)

        pr = PullRequest(
            number=result["number"],
            title=result["title"],
            url=result["url"],
            html_url=result["html_url"],
            state=result["state"],
            head=result["head"]["ref"],
            base=result["base"]["ref"]
        )

        logger.info(f"Created PR #{pr.number}: {pr.title}")
        return pr

    def create_pr_with_checklist(
        self,
        title: str,
        description: str,
        head: str,
        base: str = "main",
        checklist_items: Optional[List[str]] = None,
        issues: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None
    ) -> PullRequest:
        """
        Create PR with review checklist.

        Args:
            title: PR title
            description: PR description
            head: Source branch
            base: Target branch
            checklist_items: Review checklist items
            issues: Related issue numbers
            labels: Labels to add
            reviewers: Reviewers to assign

        Returns:
            PullRequest object
        """
        # Build PR body
        body_parts = [description]

        # Add issue references
        if issues:
            body_parts.append("\n## Related Issues")
            for issue in issues:
                issue_num = issue if issue.startswith("#") else f"#{issue}"
                body_parts.append(f"- Closes {issue_num}")

        # Add checklist
        if checklist_items:
            body_parts.append("\n## Review Checklist")
            for item in checklist_items:
                body_parts.append(f"- [ ] {item}")
        else:
            # Default checklist
            body_parts.append("\n## Review Checklist")
            body_parts.append("- [ ] Code follows project style guidelines")
            body_parts.append("- [ ] Tests pass locally")
            body_parts.append("- [ ] Documentation updated")
            body_parts.append("- [ ] No breaking changes")

        body = "\n".join(body_parts)

        # Create PR
        pr = self.create_pr(
            title=title,
            body=body,
            head=head,
            base=base
        )

        # Add labels
        if labels:
            self.add_labels(pr.number, labels)

        # Request reviewers
        if reviewers:
            self.request_reviewers(pr.number, reviewers)

        return pr

    def get_pr(self, pr_number: int) -> PullRequest:
        """
        Get pull request.

        Args:
            pr_number: PR number

        Returns:
            PullRequest object
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}"
        result = self._request("GET", endpoint)

        return PullRequest(
            number=result["number"],
            title=result["title"],
            url=result["url"],
            html_url=result["html_url"],
            state=result["state"],
            head=result["head"]["ref"],
            base=result["base"]["ref"]
        )

    def comment_on_pr(self, pr_number: int, comment: str):
        """
        Add comment to PR.

        Args:
            pr_number: PR number
            comment: Comment text
        """
        endpoint = f"/repos/{self.repo}/issues/{pr_number}/comments"

        data = {"body": comment}
        self._request("POST", endpoint, data=data)

        logger.info(f"Added comment to PR #{pr_number}")

    def add_labels(self, pr_number: int, labels: List[str]):
        """
        Add labels to PR.

        Args:
            pr_number: PR number
            labels: Label names
        """
        endpoint = f"/repos/{self.repo}/issues/{pr_number}/labels"

        data = {"labels": labels}
        self._request("POST", endpoint, data=data)

        logger.info(f"Added labels to PR #{pr_number}: {', '.join(labels)}")

    def request_reviewers(
        self,
        pr_number: int,
        reviewers: List[str],
        team_reviewers: Optional[List[str]] = None
    ):
        """
        Request reviewers for PR.

        Args:
            pr_number: PR number
            reviewers: List of GitHub usernames
            team_reviewers: List of team slugs
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}/requested_reviewers"

        data = {"reviewers": reviewers}

        if team_reviewers:
            data["team_reviewers"] = team_reviewers

        self._request("POST", endpoint, data=data)

        logger.info(f"Requested reviewers for PR #{pr_number}: {', '.join(reviewers)}")

    def merge_pr(
        self,
        pr_number: int,
        merge_method: str = "squash",
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None
    ):
        """
        Merge pull request.

        Args:
            pr_number: PR number
            merge_method: "merge", "squash", or "rebase"
            commit_title: Optional commit title
            commit_message: Optional commit message
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}/merge"

        data = {"merge_method": merge_method}

        if commit_title:
            data["commit_title"] = commit_title

        if commit_message:
            data["commit_message"] = commit_message

        self._request("PUT", endpoint, data=data)

        logger.info(f"Merged PR #{pr_number} using {merge_method}")

    def close_pr(self, pr_number: int):
        """
        Close pull request without merging.

        Args:
            pr_number: PR number
        """
        endpoint = f"/repos/{self.repo}/pulls/{pr_number}"

        data = {"state": "closed"}
        self._request("PATCH", endpoint, data=data)

        logger.info(f"Closed PR #{pr_number}")

    def list_prs(
        self,
        state: str = "open",
        base: Optional[str] = None,
        head: Optional[str] = None
    ) -> List[PullRequest]:
        """
        List pull requests.

        Args:
            state: "open", "closed", or "all"
            base: Filter by base branch
            head: Filter by head branch

        Returns:
            List of PullRequest objects
        """
        endpoint = f"/repos/{self.repo}/pulls"

        params = {"state": state}

        if base:
            params["base"] = base

        if head:
            params["head"] = head

        results = self._request("GET", endpoint, params=params)

        return [
            PullRequest(
                number=pr["number"],
                title=pr["title"],
                url=pr["url"],
                html_url=pr["html_url"],
                state=pr["state"],
                head=pr["head"]["ref"],
                base=pr["base"]["ref"]
            )
            for pr in results
        ]

    def get_issue(self, issue_number: int) -> Issue:
        """
        Get issue information.

        Args:
            issue_number: Issue number

        Returns:
            Issue object
        """
        endpoint = f"/repos/{self.repo}/issues/{issue_number}"
        result = self._request("GET", endpoint)

        return Issue(
            number=result["number"],
            title=result["title"],
            state=result["state"],
            labels=[label["name"] for label in result.get("labels", [])]
        )

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Issue:
        """
        Create issue.

        Args:
            title: Issue title
            body: Issue description
            labels: Labels to add
            assignees: Users to assign

        Returns:
            Issue object
        """
        endpoint = f"/repos/{self.repo}/issues"

        data = {
            "title": title,
            "body": body
        }

        if labels:
            data["labels"] = labels

        if assignees:
            data["assignees"] = assignees

        result = self._request("POST", endpoint, data=data)

        logger.info(f"Created issue #{result['number']}: {result['title']}")

        return Issue(
            number=result["number"],
            title=result["title"],
            state=result["state"],
            labels=[label["name"] for label in result.get("labels", [])]
        )

    def get_commit_status(self, ref: str) -> Dict:
        """
        Get commit status.

        Args:
            ref: Commit SHA or branch name

        Returns:
            Status information
        """
        endpoint = f"/repos/{self.repo}/commits/{ref}/status"
        return self._request("GET", endpoint)

    def create_release(
        self,
        tag_name: str,
        name: str,
        body: str,
        draft: bool = False,
        prerelease: bool = False
    ) -> Dict:
        """
        Create release.

        Args:
            tag_name: Tag name
            name: Release name
            body: Release notes
            draft: Create as draft
            prerelease: Mark as prerelease

        Returns:
            Release information
        """
        endpoint = f"/repos/{self.repo}/releases"

        data = {
            "tag_name": tag_name,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease
        }

        result = self._request("POST", endpoint, data=data)

        logger.info(f"Created release: {name} ({tag_name})")
        return result
