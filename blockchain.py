"""
Custom blockchain implementation for immutable password operation audit trail.
"""

import hashlib
import json
from typing import List, Optional, Tuple

import config
import database
from models import Block, utc_now_iso


class Blockchain:
    """
    Proof-of-work blockchain recording vault password operations.

    Each block links to the previous block via SHA-256 hash, creating an
    immutable audit trail for Add, Update, and Delete actions.
    """

    def __init__(self, difficulty: int = config.BLOCKCHAIN_DIFFICULTY):
        self.difficulty = difficulty
        self.prefix = "0" * difficulty

    @staticmethod
    def calculate_hash(
        block_number: int,
        timestamp: str,
        website: str,
        action: str,
        user: str,
        previous_hash: str,
        nonce: int,
    ) -> str:
        """Compute SHA-256 hash of block data."""
        block_data = {
            "block_number": block_number,
            "timestamp": timestamp,
            "website": website,
            "action": action,
            "user": user,
            "previous_hash": previous_hash,
            "nonce": nonce,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def create_genesis_block(self, username: str) -> Block:
        """Create and persist the first block in the chain."""
        timestamp = utc_now_iso()
        nonce = 0
        previous_hash = "0" * 64
        current_hash = self.calculate_hash(
            0, timestamp, "Genesis", "Genesis Block", username, previous_hash, nonce
        )
        while not current_hash.startswith(self.prefix):
            nonce += 1
            current_hash = self.calculate_hash(
                0, timestamp, "Genesis", "Genesis Block", username, previous_hash, nonce
            )

        block = Block(
            block_number=0,
            timestamp=timestamp,
            website="Genesis",
            action="Genesis Block",
            user=username,
            previous_hash=previous_hash,
            current_hash=current_hash,
            nonce=nonce,
        )
        database.save_block(block)
        return block

    def add_block(self, website: str, action: str, username: str) -> Block:
        """Mine and append a new block for a password operation."""
        last_block = database.get_last_block()
        if last_block is None:
            return self.create_genesis_block(username)

        block_number = last_block.block_number + 1
        timestamp = utc_now_iso()
        previous_hash = last_block.current_hash
        nonce = 0
        current_hash = self.calculate_hash(
            block_number, timestamp, website, action, username, previous_hash, nonce
        )
        while not current_hash.startswith(self.prefix):
            nonce += 1
            current_hash = self.calculate_hash(
                block_number, timestamp, website, action, username, previous_hash, nonce
            )

        block = Block(
            block_number=block_number,
            timestamp=timestamp,
            website=website,
            action=action,
            user=username,
            previous_hash=previous_hash,
            current_hash=current_hash,
            nonce=nonce,
        )
        database.save_block(block)
        return block

    def verify_chain(self, blocks: Optional[List[Block]] = None) -> Tuple[bool, str]:
        """
        Verify blockchain integrity.

        Returns (is_valid, message).
        """
        if blocks is None:
            blocks = database.get_all_blocks()

        if not blocks:
            return True, "Blockchain is empty."

        genesis = blocks[0]
        expected_genesis_hash = self.calculate_hash(
            genesis.block_number,
            genesis.timestamp,
            genesis.website,
            genesis.action,
            genesis.user,
            genesis.previous_hash,
            genesis.nonce,
        )
        if genesis.current_hash != expected_genesis_hash:
            return False, f"Genesis block hash mismatch at block {genesis.block_number}."

        if genesis.previous_hash != "0" * 64:
            return False, "Genesis block has invalid previous hash."

        for index in range(1, len(blocks)):
            current = blocks[index]
            previous = blocks[index - 1]

            if current.block_number != previous.block_number + 1:
                return False, f"Block index mismatch at block {current.block_number}."

            if current.previous_hash != previous.current_hash:
                return False, f"Chain broken at block {current.block_number}: previous hash mismatch."

            expected_hash = self.calculate_hash(
                current.block_number,
                current.timestamp,
                current.website,
                current.action,
                current.user,
                current.previous_hash,
                current.nonce,
            )
            if current.current_hash != expected_hash:
                return False, f"Hash tampered at block {current.block_number}."

            if not current.current_hash.startswith(self.prefix):
                return False, f"Invalid proof-of-work at block {current.block_number}."

        return True, "Blockchain verified successfully."


blockchain = Blockchain()
