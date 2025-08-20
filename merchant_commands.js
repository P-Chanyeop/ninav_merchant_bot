const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const { MerchantParser } = require('./merchant_parser');

// 상인 정보 명령어들
const merchantCommands = {
    // 전체 상인 목록 조회
    merchants: {
        data: new SlashCommandBuilder()
            .setName('상인목록')
            .setDescription('모든 떠돌이 상인 정보를 조회합니다'),
        
        async execute(interaction, apiData) {
            const parser = new MerchantParser(apiData);
            const merchants = parser.getMerchantsByRegion();
            
            const embed = new EmbedBuilder()
                .setTitle('🏪 떠돌이 상인 목록')
                .setColor(0x0099FF)
                .setTimestamp();
            
            merchants.forEach(merchant => {
                embed.addFields({
                    name: `📍 ${merchant.지역명}`,
                    value: `**상인:** ${merchant.상인명}\n**주요 아이템:** ${merchant.주요아이템.join(', ') || '없음'}`,
                    inline: true
                });
            });
            
            await interaction.reply({ embeds: [embed] });
        }
    },

    // 오늘의 스케줄 조회
    schedule: {
        data: new SlashCommandBuilder()
            .setName('상인스케줄')
            .setDescription('오늘의 상인 스케줄을 조회합니다')
            .addStringOption(option =>
                option.setName('요일')
                    .setDescription('특정 요일의 스케줄을 조회합니다 (선택사항)')
                    .addChoices(
                        { name: '일요일', value: '0' },
                        { name: '월요일', value: '1' },
                        { name: '화요일', value: '2' },
                        { name: '수요일', value: '3' },
                        { name: '목요일', value: '4' },
                        { name: '금요일', value: '5' },
                        { name: '토요일', value: '6' }
                    )),
        
        async execute(interaction, apiData) {
            const parser = new MerchantParser(apiData);
            const scheduleData = parser.getScheduleByDay();
            
            const dayNames = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
            const selectedDay = interaction.options.getString('요일');
            const targetDay = selectedDay ? dayNames[parseInt(selectedDay)] : dayNames[new Date().getDay()];
            
            const daySchedule = scheduleData[targetDay];
            
            const embed = new EmbedBuilder()
                .setTitle(`📅 ${targetDay} 상인 스케줄`)
                .setColor(0x00FF00)
                .setTimestamp();
            
            if (daySchedule && daySchedule.length > 0) {
                daySchedule.forEach((schedule, index) => {
                    embed.addFields({
                        name: `⏰ ${schedule.시작시간} (${schedule.지속시간})`,
                        value: schedule.상인들.join('\n'),
                        inline: false
                    });
                });
            } else {
                embed.setDescription('해당 요일에는 상인이 없습니다.');
            }
            
            await interaction.reply({ embeds: [embed] });
        }
    },

    // 특정 상인 정보 조회
    merchantInfo: {
        data: new SlashCommandBuilder()
            .setName('상인정보')
            .setDescription('특정 상인의 상세 정보를 조회합니다')
            .addStringOption(option =>
                option.setName('상인명')
                    .setDescription('조회할 상인 이름 또는 지역명')
                    .setRequired(true)),
        
        async execute(interaction, apiData) {
            const parser = new MerchantParser(apiData);
            const merchantName = interaction.options.getString('상인명');
            const merchantSchedule = parser.getMerchantSchedule(merchantName);
            
            if (!merchantSchedule) {
                await interaction.reply('해당 상인을 찾을 수 없습니다.');
                return;
            }
            
            const region = parser.regions.find(r => 
                r.name.includes(merchantName) || r.npcName.includes(merchantName)
            );
            
            const embed = new EmbedBuilder()
                .setTitle(`🏪 ${merchantSchedule.상인명} (${merchantSchedule.지역명})`)
                .setColor(0xFF9900)
                .setTimestamp();
            
            // 스케줄 정보
            const scheduleText = merchantSchedule.스케줄
                .map(s => `**${s.요일}:** ${s.시작시간} (${s.지속시간})`)
                .join('\n');
            
            embed.addFields({
                name: '📅 출현 스케줄',
                value: scheduleText,
                inline: false
            });
            
            // 판매 아이템 정보
            if (region) {
                const items = region.items
                    .filter(item => !item.hidden)
                    .sort((a, b) => b.grade - a.grade)
                    .slice(0, 10)
                    .map(item => `${parser.getGradeText(item.grade)} ${item.name}`)
                    .join('\n');
                
                embed.addFields({
                    name: '🛍️ 판매 아이템',
                    value: items || '정보 없음',
                    inline: false
                });
            }
            
            await interaction.reply({ embeds: [embed] });
        }
    },

    // 아이템 검색
    itemSearch: {
        data: new SlashCommandBuilder()
            .setName('아이템검색')
            .setDescription('특정 아이템을 판매하는 상인을 찾습니다')
            .addStringOption(option =>
                option.setName('아이템명')
                    .setDescription('검색할 아이템 이름')
                    .setRequired(true)),
        
        async execute(interaction, apiData) {
            const parser = new MerchantParser(apiData);
            const itemName = interaction.options.getString('아이템명');
            const sellers = parser.getItemSellers(itemName);
            
            const embed = new EmbedBuilder()
                .setTitle(`🔍 "${itemName}" 검색 결과`)
                .setColor(0xFF0099)
                .setTimestamp();
            
            if (sellers.length > 0) {
                sellers.forEach(seller => {
                    embed.addFields({
                        name: `📍 ${seller.지역명} - ${seller.상인명}`,
                        value: `**아이템:** ${seller.아이템명}\n**등급:** ${seller.등급}\n**타입:** ${seller.타입}`,
                        inline: true
                    });
                });
            } else {
                embed.setDescription('해당 아이템을 판매하는 상인을 찾을 수 없습니다.');
            }
            
            await interaction.reply({ embeds: [embed] });
        }
    },

    // 현재 활성 상인 조회
    activeMerchants: {
        data: new SlashCommandBuilder()
            .setName('현재상인')
            .setDescription('현재 시간에 활성화된 상인들을 조회합니다'),
        
        async execute(interaction, apiData) {
            const parser = new MerchantParser(apiData);
            const activeMerchants = parser.getCurrentActiveMerchants();
            
            const embed = new EmbedBuilder()
                .setTitle('🟢 현재 활성 상인')
                .setColor(0x00FF00)
                .setTimestamp();
            
            if (activeMerchants.length > 0) {
                activeMerchants.forEach(merchant => {
                    embed.addFields({
                        name: `⏰ ${merchant.시작시간} (${merchant.지속시간})`,
                        value: merchant.활성상인들.join('\n'),
                        inline: false
                    });
                });
            } else {
                embed.setDescription('현재 활성화된 상인이 없습니다.');
            }
            
            await interaction.reply({ embeds: [embed] });
        }
    }
};

module.exports = merchantCommands;
