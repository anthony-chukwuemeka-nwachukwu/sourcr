"""
Pytest configuration.

Load .env before tests are collected so env-driven settings are available at
collection time — notably RUN_LIVE (which decides whether the opt-in live
integration test is skipped) and the API keys that test needs.
"""

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
