"""
Test suite for Blockchain-Based Secure Password Vault.
"""

import os
import re
import tempfile
import unittest

import config
import database
from app import create_app
from blockchain import Blockchain
from encryption import EncryptionManager
from password_generator import generate_password
from password_strength import analyze_password, STRENGTH_STRONG, STRENGTH_WEAK
from utils import hash_password, verify_password


class TestPasswordStrength(unittest.TestCase):
    def test_weak_password(self):
        result = analyze_password("abc")
        self.assertEqual(result["strength"], STRENGTH_WEAK)

    def test_strong_password(self):
        result = analyze_password("R8@mL2#Az!7Qx9")
        self.assertEqual(result["strength"], STRENGTH_STRONG)
        self.assertGreater(result["entropy"], 50)


class TestPasswordGenerator(unittest.TestCase):
    def test_generate_default(self):
        result = generate_password()
        self.assertEqual(len(result["password"]), 16)
        self.assertTrue(any(c.isupper() for c in result["password"]))

    def test_generate_custom_length(self):
        result = generate_password(length=24, use_symbols=False)
        self.assertEqual(len(result["password"]), 24)


class TestEncryption(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.key_file = os.path.join(self.temp_dir, "secret.key")
        self.manager = EncryptionManager(key_file=self.key_file)

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "MySecretP@ssw0rd!"
        encrypted = self.manager.encrypt(plaintext)
        self.assertNotEqual(encrypted, plaintext)
        decrypted = self.manager.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)


class TestBlockchain(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        config.DATABASE_PATH = self.temp_db.name
        database.init_db()
        self.chain = Blockchain(difficulty=1)

    def tearDown(self):
        os.unlink(self.temp_db.name)

    def test_genesis_and_add_block(self):
        genesis = self.chain.create_genesis_block("testuser")
        self.assertEqual(genesis.block_number, 0)
        self.assertTrue(genesis.current_hash.startswith("0"))

        block = self.chain.add_block("github.com", "Add Password", "testuser")
        self.assertEqual(block.block_number, 1)
        self.assertEqual(block.previous_hash, genesis.current_hash)

    def test_verify_valid_chain(self):
        self.chain.create_genesis_block("testuser")
        self.chain.add_block("github.com", "Add Password", "testuser")
        blocks = database.get_all_blocks()
        valid, message = self.chain.verify_chain(blocks)
        self.assertTrue(valid)

    def test_verify_tampered_chain(self):
        self.chain.create_genesis_block("testuser")
        self.chain.add_block("github.com", "Add Password", "testuser")
        blocks = database.get_all_blocks()
        blocks[1].current_hash = "tampered" + blocks[1].current_hash[8:]
        valid, _ = self.chain.verify_chain(blocks)
        self.assertFalse(valid)


class TestAuth(unittest.TestCase):
    def test_bcrypt_hash_verify(self):
        password = "TestPass123"
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong", hashed))


class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, "test.db")
        self.key_file = os.path.join(self.temp_dir, "secret.key")
        config.DATABASE_PATH = self.temp_db
        config.SECRET_KEY_FILE = self.key_file
        config.INSTANCE_DIR = self.temp_dir
        database.init_db()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_index_redirects_to_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    def test_register_and_login(self):
        get_resp = self.client.get("/register")
        match = re.search(r'name="csrf_token" value="([^"]+)"', get_resp.data.decode())
        self.assertIsNotNone(match)
        csrf_token = match.group(1)
        response = self.client.post(
            "/register",
            data={
                "csrf_token": csrf_token,
                "username": "testuser",
                "email": "test@example.com",
                "password": "SecurePass1",
                "confirm_password": "SecurePass1",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)


if __name__ == "__main__":
    unittest.main()
