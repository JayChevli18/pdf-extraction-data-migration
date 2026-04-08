import unittest

from profile_backend.src.profile_backend.domain.organize import (
    filename_from_name,
    gender_folder,
    normalize_dob,
    year_folder_from_dob,
)


class TestDomainHelpers(unittest.TestCase):
    def test_year_folder_from_dob(self):
        self.assertEqual(year_folder_from_dob("1995-01-20"), "1995")
        self.assertEqual(year_folder_from_dob("20-01-1995"), "1995")
        self.assertEqual(year_folder_from_dob("abc"), "Unknown")

    def test_normalize_dob(self):
        self.assertEqual(normalize_dob("15-01-1990"), "1990-01-15")
        self.assertEqual(normalize_dob("15/01/1990"), "1990-01-15")

    def test_gender_folder(self):
        self.assertEqual(gender_folder("male"), "Male")
        self.assertEqual(gender_folder("f"), "Female")
        self.assertEqual(gender_folder(""), "Unknown")

    def test_filename_from_name(self):
        self.assertEqual(
            filename_from_name("Jane Doe", "{first}_{last}_Profile"),
            "Jane_Doe_Profile",
        )
        self.assertEqual(
            filename_from_name("", "{first}_{last}_Profile"),
            "Unknown_Unknown_Profile",
        )
