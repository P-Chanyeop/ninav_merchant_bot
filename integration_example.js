// 기존 봇에 상인 기능 통합 예시

const { Client, GatewayIntentBits, Collection } = require('discord.js');
const merchantCommands = require('./merchant_commands');
const axios = require('axios'); // API 호출용

class MerchantBot {
    constructor() {
        this.client = new Client({ 
            intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages] 
        });
        this.commands = new Collection();
        this.merchantData = null;
        
        this.setupCommands();
        this.setupEvents();
    }

    setupCommands() {
        // 상인 관련 명령어들 등록
        Object.entries(merchantCommands).forEach(([name, command]) => {
            this.commands.set(command.data.name, command);
        });
    }

    setupEvents() {
        this.client.once('ready', () => {
            console.log(`${this.client.user.tag}로 로그인했습니다!`);
            this.updateMerchantData(); // 봇 시작시 데이터 로드
            
            // 1시간마다 데이터 업데이트
            setInterval(() => {
                this.updateMerchantData();
            }, 60 * 60 * 1000);
        });

        this.client.on('interactionCreate', async interaction => {
            if (!interaction.isChatInputCommand()) return;

            const command = this.commands.get(interaction.commandName);
            if (!command) return;

            try {
                // 상인 데이터가 없으면 먼저 로드
                if (!this.merchantData) {
                    await interaction.deferReply();
                    await this.updateMerchantData();
                    await command.execute(interaction, this.merchantData);
                } else {
                    await command.execute(interaction, this.merchantData);
                }
            } catch (error) {
                console.error('명령어 실행 중 오류:', error);
                const reply = { content: '명령어 실행 중 오류가 발생했습니다.', ephemeral: true };
                
                if (interaction.deferred) {
                    await interaction.editReply(reply);
                } else {
                    await interaction.reply(reply);
                }
            }
        });
    }

    // API에서 상인 데이터 업데이트
    async updateMerchantData() {
        try {
            // 실제 API 엔드포인트로 교체 필요
            const response = await axios.get('YOUR_API_ENDPOINT_HERE');
            this.merchantData = response.data;
            console.log('상인 데이터가 업데이트되었습니다.');
        } catch (error) {
            console.error('상인 데이터 업데이트 실패:', error);
            
            // 실패시 기본 데이터 사용 (옵션)
            if (!this.merchantData) {
                this.merchantData = this.getDefaultMerchantData();
            }
        }
    }

    // 기본 데이터 (API 실패시 대체용)
    getDefaultMerchantData() {
        return {
            pageProps: {
                initialData: {
                    scheme: {
                        schedules: [],
                        regions: []
                    }
                }
            }
        };
    }

    // 명령어 등록 (Discord Developer Portal에서 등록 필요)
    async registerCommands() {
        const commands = Object.values(merchantCommands).map(cmd => cmd.data.toJSON());
        
        try {
            console.log('슬래시 명령어 등록 중...');
            await this.client.application.commands.set(commands);
            console.log('슬래시 명령어 등록 완료!');
        } catch (error) {
            console.error('명령어 등록 실패:', error);
        }
    }

    async start(token) {
        await this.client.login(token);
        await this.registerCommands();
    }
}

// 사용 예시
const bot = new MerchantBot();
// bot.start('YOUR_BOT_TOKEN');

module.exports = MerchantBot;
