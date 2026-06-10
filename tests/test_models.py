import unittest
from models import Job

class TestJobModel(unittest.TestCase):
    def test_valid_job_instantiation(self):
        job = Job(
            title="Python Developer",
            company="Tech Corp",
            location="Remote",
            link="https://example.com/job/1",
            source_platform="RemoteOK",
            salary="$100k - $120k"
        )
        self.assertEqual(job.title, "Python Developer")
        self.assertEqual(job.salary, "$100k - $120k")

    def test_missing_optional_salary(self):
        job = Job(
            title="Python Developer",
            company="Tech Corp",
            location="Remote",
            link="https://example.com/job/2",
            source_platform="Wellfound"
        )
        self.assertIsNone(job.salary)

    def test_data_type_coercion(self):
        # Simulating a scraper returning an integer instead of a string
        job = Job(
            title=12345,
            company=None,
            location="Remote",
            link="https://example.com",
            source_platform="Naukri"
        )
        self.assertEqual(job.title, "12345")
        self.assertEqual(job.company, "Unknown Company")

    def test_extremely_long_strings(self):
        long_str = "A" * 10000
        job = Job(
            title=long_str,
            company="Long Corp",
            location="Remote",
            link="https://example.com",
            source_platform="RemoteOK"
        )
        self.assertEqual(len(job.title), 10000)

if __name__ == '__main__':
    unittest.main()
