#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skill" / "hk-auto-apply" / "scripts"))
import dedup  # noqa: E402


class DedupTests(unittest.TestCase):
    def test_same_url_with_tracking_params(self):
        job = {
            "company": "Example Bank",
            "title": "Relationship Manager",
            "url": "https://hk.jobsdb.com/job/12345?utm_source=share",
            "platform": "JobsDB",
        }
        tracker = [
            {
                "company": "Other Co",
                "title": "Other role",
                "url": "https://hk.jobsdb.com/job/12345",
                "platform": "JobsDB",
                "status": "已投递",
            }
        ]
        hit = dedup.find_duplicate(job, tracker)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["reason"], "same_url")

    def test_arm_matches_assistant_relationship_manager(self):
        job = {
            "company": "Noah Holdings Limited",
            "title": "ARM",
            "url": "https://www.linkedin.com/jobs/view/999",
            "platform": "LinkedIn",
        }
        tracker = [
            {
                "company": "Noah Holdings Ltd",
                "title": "Assistant Relationship Manager",
                "url": "https://hk.jobsdb.com/job/888",
                "platform": "JobsDB",
                "status": "已投递",
            }
        ]
        hit = dedup.find_duplicate(job, tracker)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["reason"], "same_company_and_title")

    def test_same_company_different_roles_are_not_duplicates(self):
        job = {
            "company": "Example Bank Limited",
            "title": "KYC Analyst",
            "url": "https://www.linkedin.com/jobs/view/1",
            "platform": "LinkedIn",
        }
        tracker = [
            {
                "company": "Example Bank Ltd",
                "title": "Relationship Manager",
                "url": "https://hk.jobsdb.com/job/2",
                "platform": "JobsDB",
                "status": "已投递",
            }
        ]
        self.assertIsNone(dedup.find_duplicate(job, tracker))

    def test_linkedin_current_job_id(self):
        job = {"url": "https://www.linkedin.com/jobs/search/?currentJobId=4242"}
        record = {"url": "https://www.linkedin.com/jobs/view/4242/"}
        self.assertEqual(dedup.duplicate_reason(job, record), "same_url")


if __name__ == "__main__":
    unittest.main()
