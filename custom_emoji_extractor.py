#!/usr/bin/env python3
"""
Mattermost Custom Emoji Extractor

This script connects to the Mattermost API to retrieve and download all custom emojis.
"""

import requests
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import time

class MattermostEmojiExtractor:
    def __init__(self, server_url: str, access_token: str):
        """
        Initialize the Mattermost emoji extractor.
        
        Args:
            server_url: Mattermost server URL (e.g., 'https://your-mattermost.com')
            access_token: Personal access token or bot token
        """
        self.server_url = server_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self) -> bool:
        """Test the connection to Mattermost API."""
        try:
            response = self.session.get(f'{self.server_url}/api/v4/users/me')
            if response.status_code == 200:
                user_data = response.json()
                print(f"✓ Connected successfully as: {user_data.get('username', 'Unknown')}")
                return True
            else:
                print(f"✗ Connection failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def get_custom_emojis(self, page: int = 0, per_page: int = 200) -> List[Dict]:
        """
        Retrieve custom emojis from Mattermost.
        
        Args:
            page: Page number (0-based)
            per_page: Number of emojis per page (max 200)
            
        Returns:
            List of emoji dictionaries
        """
        params = {
            'page': page,
            'per_page': per_page,
            'sort': 'name'
        }
        
        try:
            response = self.session.get(
                f'{self.server_url}/api/v4/emoji',
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching emojis: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error fetching emojis: {e}")
            return []
    
    def get_all_custom_emojis(self) -> List[Dict]:
        """Retrieve all custom emojis by paginating through results."""
        all_emojis = []
        page = 0
        per_page = 200
        
        print("Fetching custom emojis...")
        
        while True:
            emojis = self.get_custom_emojis(page=page, per_page=per_page)
            
            if not emojis:
                break
                
            all_emojis.extend(emojis)
            print(f"Retrieved {len(emojis)} emojis from page {page + 1}")
            
            if len(emojis) < per_page:
                break
                
            page += 1
            time.sleep(0.1)  # Be nice to the API
        
        print(f"✓ Total custom emojis found: {len(all_emojis)}")
        return all_emojis
    
    def download_emoji_image(self, emoji_id: str, emoji_name: str, download_dir: str) -> bool:
        """
        Download an emoji image.
        
        Args:
            emoji_id: Emoji ID
            emoji_name: Emoji name (for filename)
            download_dir: Directory to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.get(
                f'{self.server_url}/api/v4/emoji/{emoji_id}/image',
                stream=True
            )
            
            if response.status_code == 200:
                # Determine file extension from content type
                content_type = response.headers.get('content-type', '')
                if 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                else:
                    ext = '.png'  # Default to PNG
                
                filename = f"{emoji_name}{ext}"
                filepath = os.path.join(download_dir, filename)
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return True
            else:
                print(f"Failed to download {emoji_name}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error downloading {emoji_name}: {e}")
            return False
    
    def extract_emojis(self, download_dir: str = "mattermost_emojis") -> None:
        """
        Extract all custom emojis from Mattermost.
        
        Args:
            download_dir: Directory to save emojis and metadata
        """
        # Create download directory
        Path(download_dir).mkdir(exist_ok=True)
        
        # Test connection first
        if not self.test_connection():
            return
        
        # Get all custom emojis
        emojis = self.get_all_custom_emojis()
        
        if not emojis:
            print("No custom emojis found or unable to retrieve emojis.")
            return
        
        # Save emoji metadata
        metadata_file = os.path.join(download_dir, "emoji_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(emojis, f, indent=2)
        print(f"✓ Saved emoji metadata to {metadata_file}")
        
        # Download emoji images
        print(f"\nDownloading emoji images to {download_dir}...")
        success_count = 0
        
        for i, emoji in enumerate(emojis, 1):
            emoji_id = emoji['id']
            emoji_name = emoji['name']
            
            print(f"[{i}/{len(emojis)}] Downloading {emoji_name}...", end=" ")
            
            if self.download_emoji_image(emoji_id, emoji_name, download_dir):
                success_count += 1
                print("✓")
            else:
                print("✗")
            
            # Small delay to be respectful to the API
            time.sleep(0.1)
        
        print(f"\n✓ Downloaded {success_count}/{len(emojis)} emojis successfully!")
        print(f"✓ Files saved to: {os.path.abspath(download_dir)}")


def main():
    """Main function to run the emoji extractor."""
    print("Mattermost Custom Emoji Extractor")
    print("=" * 40)
    
    # Configuration - UPDATE THESE VALUES
    MATTERMOST_URL = "https://your-mattermost-server.com"  # Update this
    ACCESS_TOKEN = "your-access-token-here"  # Update this
    DOWNLOAD_DIR = "mattermost_emojis"  # Optional: change download directory
    
    # Validate configuration
    if MATTERMOST_URL == "https://your-mattermost-server.com" or ACCESS_TOKEN == "your-access-token-here":
        print("⚠️  Please update the configuration variables:")
        print("   - MATTERMOST_URL: Your Mattermost server URL")
        print("   - ACCESS_TOKEN: Your personal access token")
        print("\nTo get a personal access token:")
        print("1. Go to Account Settings → Security → Personal Access Tokens")
        print("2. Create a new token with appropriate permissions")
        print("3. Copy the token and update the ACCESS_TOKEN variable")
        return
    
    # Initialize extractor
    extractor = MattermostEmojiExtractor(MATTERMOST_URL, ACCESS_TOKEN)
    
    # Extract emojis
    extractor.extract_emojis(DOWNLOAD_DIR)


if __name__ == "__main__":
    main()
