#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로스트아크 캐릭터 정보 조회 디스코드 봇
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import requests
import urllib.parse

# Discord 봇 관련
import discord
from discord.ext import commands

class LostArkCharacterAPI:
    """로스트아크 캐릭터 정보 조회 API 클래스"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://developer-lostark.game.onstove.com"
        self.headers = {
            'accept': 'application/json',
            'authorization': f'bearer {api_key}'
        }
    
    async def get_character_info(self, character_name: str) -> Optional[Dict]:
        """캐릭터 기본 정보 조회"""
        try:
            encoded_name = urllib.parse.quote(character_name)
            url = f"{self.base_url}/characters/{encoded_name}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"API 오류: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"캐릭터 정보 조회 오류: {e}")
            return None
    
    async def get_character_siblings(self, character_name: str) -> Optional[List[Dict]]:
        """캐릭터 원정대 정보 조회"""
        try:
            encoded_name = urllib.parse.quote(character_name)
            url = f"{self.base_url}/characters/{encoded_name}/siblings"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"API 오류: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"원정대 정보 조회 오류: {e}")
            return None

class CharacterInfoBot:
    """캐릭터 정보 조회 디스코드 봇"""
    
    def __init__(self, discord_token: str, lostark_api_key: str):
        self.discord_token = discord_token
        self.lostark_api = LostArkCharacterAPI(lostark_api_key)
        
        # Discord 봇 설정
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='/', intents=intents)
        
        self.setup_commands()
    
    def setup_commands(self):
        """디스코드 명령어 설정"""
        
        @self.bot.event
        async def on_ready():
            print(f'✅ 캐릭터 정보 봇 로그인: {self.bot.user}')
            print('사용 가능한 명령어: /캐릭터정보 캐릭터명')
        
        @self.bot.command(name='캐릭터정보')
        async def character_info(ctx, *, character_name: str = None):
            """캐릭터 정보 조회 명령어"""
            if not character_name:
                await ctx.send("❌ 캐릭터명을 입력해주세요!\n사용법: `/캐릭터정보 캐릭터명`")
                return
            
            # 로딩 메시지
            loading_msg = await ctx.send(f"🔍 `{character_name}` 캐릭터 정보를 조회중...")
            
            try:
                # 캐릭터 기본 정보 조회
                char_info = await self.lostark_api.get_character_info(character_name)
                
                if not char_info:
                    await loading_msg.edit(content=f"❌ `{character_name}` 캐릭터를 찾을 수 없습니다.")
                    return
                
                # 원정대 정보 조회
                siblings_info = await self.lostark_api.get_character_siblings(character_name)
                
                # Discord Embed 생성
                embed = await self.create_character_embed(char_info, siblings_info)
                
                await loading_msg.edit(content="", embed=embed)
                
            except Exception as e:
                await loading_msg.edit(content=f"❌ 오류가 발생했습니다: {str(e)}")
                print(f"캐릭터 정보 조회 오류: {e}")
        
        @self.bot.command(name='도움말', aliases=['help'])
        async def help_command(ctx):
            """도움말 명령어"""
            embed = discord.Embed(
                title="🎮 로스트아크 캐릭터 정보 봇",
                description="로스트아크 공식 API를 사용한 캐릭터 정보 조회 봇입니다.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 사용 가능한 명령어",
                value="`/캐릭터정보 캐릭터명` - 캐릭터 정보 조회\n`/도움말` - 이 도움말 표시",
                inline=False
            )
            
            embed.add_field(
                name="💡 사용 예시",
                value="`/캐릭터정보 유우니유니`",
                inline=False
            )
            
            embed.set_footer(text="로스트아크 공식 API 사용")
            await ctx.send(embed=embed)
    
    async def create_character_embed(self, char_info: Dict, siblings_info: Optional[List[Dict]]) -> discord.Embed:
        """캐릭터 정보 Discord Embed 생성"""
        
        # 기본 정보
        char_name = char_info.get('CharacterName', 'Unknown')
        server_name = char_info.get('ServerName', 'Unknown')
        char_class = char_info.get('CharacterClassName', 'Unknown')
        char_level = char_info.get('CharacterLevel', 0)
        item_level = char_info.get('ItemAvgLevel', 'Unknown')
        item_max_level = char_info.get('ItemMaxLevel', 'Unknown')
        
        # Embed 생성
        embed = discord.Embed(
            title=f"⚔️ {char_name}",
            description=f"**{server_name}** 서버의 **{char_class}**",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # 기본 정보 필드
        embed.add_field(
            name="📊 기본 정보",
            value=f"```\n레벨: {char_level}\n평균 아이템레벨: {item_level}\n최고 아이템레벨: {item_max_level}```",
            inline=False
        )
        
        # 원정대 정보 (있는 경우)
        if siblings_info and len(siblings_info) > 0:
            expedition_text = ""
            for sibling in siblings_info[:10]:  # 최대 10개만 표시
                sib_name = sibling.get('CharacterName', 'Unknown')
                sib_class = sibling.get('CharacterClassName', 'Unknown')
                sib_level = sibling.get('ItemAvgLevel', 'Unknown')
                expedition_text += f"{sib_name} ({sib_class}) - {sib_level}\n"
            
            if expedition_text:
                embed.add_field(
                    name="👥 원정대 캐릭터",
                    value=f"```\n{expedition_text}```",
                    inline=False
                )
        
        embed.set_footer(text="로스트아크 공식 API | 캐릭터 정보 조회")
        
        return embed
    
    def run(self):
        """봇 실행"""
        try:
            self.bot.run(self.discord_token)
        except Exception as e:
            print(f"❌ 캐릭터 정보 봇 실행 오류: {e}")

def main():
    """메인 함수"""
    print("🚀 로스트아크 캐릭터 정보 봇 시작")
    print("=" * 60)
    
    # Discord 봇 토큰 입력
    discord_token = input("Discord 봇 토큰을 입력하세요: ").strip()
    if not discord_token:
        print("❌ Discord 봇 토큰이 필요합니다!")
        return
    
    # 로스트아크 API 키 입력
    lostark_api_key = input("로스트아크 API 키를 입력하세요: ").strip()
    if not lostark_api_key:
        print("❌ 로스트아크 API 키가 필요합니다!")
        return
    
    print(f"✅ 설정 완료:")
    print(f"   - 캐릭터 정보 조회: /캐릭터정보 명령어")
    print(f"   - 데이터 소스: 로스트아크 공식 API")
    print(f"   - 도움말: /도움말")
    
    # 캐릭터정보 봇 실행
    character_bot = CharacterInfoBot(discord_token, lostark_api_key)
    character_bot.run()

if __name__ == "__main__":
    main()
