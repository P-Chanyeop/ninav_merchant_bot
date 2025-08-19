// 상인 정보 파싱 및 정리 함수들

class MerchantParser {
    constructor(apiData) {
        this.data = apiData.pageProps.initialData.scheme;
        this.schedules = this.data.schedules;
        this.regions = this.data.regions;
    }

    // 지역별 상인 정보 정리
    getMerchantsByRegion() {
        return this.regions.map(region => ({
            지역명: region.name,
            상인명: region.npcName,
            그룹: region.group,
            판매아이템수: region.items.length,
            주요아이템: this.getMainItems(region.items)
        }));
    }

    // 주요 아이템 추출 (등급 3 이상)
    getMainItems(items) {
        return items
            .filter(item => item.grade >= 3 && !item.hidden)
            .map(item => `${item.name} (${this.getGradeText(item.grade)})`)
            .slice(0, 3); // 상위 3개만
    }

    // 등급 텍스트 변환
    getGradeText(grade) {
        const gradeMap = {
            1: '일반',
            2: '고급',
            3: '희귀',
            4: '영웅',
            5: '전설'
        };
        return gradeMap[grade] || '알 수 없음';
    }

    // 요일별 스케줄 정리
    getScheduleByDay() {
        const dayNames = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
        const scheduleByDay = {};

        this.schedules.forEach(schedule => {
            const dayName = dayNames[schedule.dayOfWeek];
            if (!scheduleByDay[dayName]) {
                scheduleByDay[dayName] = [];
            }

            const merchantNames = schedule.groups.map(groupId => {
                const region = this.regions.find(r => r.group === groupId);
                return region ? `${region.name} (${region.npcName})` : `그룹 ${groupId}`;
            });

            scheduleByDay[dayName].push({
                시작시간: schedule.startTime,
                지속시간: schedule.duration,
                상인들: merchantNames
            });
        });

        return scheduleByDay;
    }

    // 특정 상인의 스케줄 조회
    getMerchantSchedule(merchantName) {
        const region = this.regions.find(r => 
            r.name.includes(merchantName) || r.npcName.includes(merchantName)
        );
        
        if (!region) return null;

        const dayNames = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
        const merchantSchedules = this.schedules
            .filter(schedule => schedule.groups.includes(region.group))
            .map(schedule => ({
                요일: dayNames[schedule.dayOfWeek],
                시작시간: schedule.startTime,
                지속시간: schedule.duration
            }));

        return {
            지역명: region.name,
            상인명: region.npcName,
            스케줄: merchantSchedules
        };
    }

    // 현재 시간 기준 활성 상인 조회
    getCurrentActiveMerchants(currentTime = new Date()) {
        const currentDay = currentTime.getDay();
        const currentTimeStr = currentTime.toTimeString().slice(0, 8);
        
        const activeSchedules = this.schedules.filter(schedule => {
            if (schedule.dayOfWeek !== currentDay) return false;
            
            const startTime = schedule.startTime;
            const [hours, minutes, seconds] = schedule.duration.split(':').map(Number);
            const durationMs = (hours * 60 + minutes) * 60 * 1000 + seconds * 1000;
            
            // 시간 계산 로직 (간단화)
            return this.isTimeInRange(currentTimeStr, startTime, durationMs);
        });

        return activeSchedules.map(schedule => ({
            시작시간: schedule.startTime,
            지속시간: schedule.duration,
            활성상인들: schedule.groups.map(groupId => {
                const region = this.regions.find(r => r.group === groupId);
                return region ? `${region.name} (${region.npcName})` : `그룹 ${groupId}`;
            })
        }));
    }

    // 시간 범위 체크 (간단한 구현)
    isTimeInRange(currentTime, startTime, durationMs) {
        // 실제 구현에서는 더 정확한 시간 계산이 필요
        return true; // 임시로 true 반환
    }

    // 아이템별 판매 상인 조회
    getItemSellers(itemName) {
        const sellers = [];
        
        this.regions.forEach(region => {
            const item = region.items.find(item => 
                item.name.includes(itemName)
            );
            
            if (item) {
                sellers.push({
                    지역명: region.name,
                    상인명: region.npcName,
                    아이템명: item.name,
                    등급: this.getGradeText(item.grade),
                    타입: this.getItemType(item.type)
                });
            }
        });
        
        return sellers;
    }

    // 아이템 타입 변환
    getItemType(type) {
        const typeMap = {
            1: '카드',
            2: '아이템',
            3: '재료'
        };
        return typeMap[type] || '알 수 없음';
    }

    // 전체 정보를 보기 좋게 포맷팅
    getFormattedSummary() {
        const merchants = this.getMerchantsByRegion();
        const schedule = this.getScheduleByDay();
        
        return {
            상인정보: merchants,
            요일별스케줄: schedule,
            총상인수: this.regions.length,
            총스케줄수: this.schedules.length
        };
    }
}

// 사용 예시 함수
function displayMerchantInfo(apiData) {
    const parser = new MerchantParser(apiData);
    
    console.log('=== 상인 정보 요약 ===');
    const summary = parser.getFormattedSummary();
    
    console.log('\n📍 지역별 상인:');
    summary.상인정보.forEach(merchant => {
        console.log(`• ${merchant.지역명}: ${merchant.상인명}`);
        console.log(`  주요 아이템: ${merchant.주요아이템.join(', ')}`);
    });
    
    console.log('\n📅 오늘의 스케줄:');
    const today = new Date().getDay();
    const dayNames = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
    const todaySchedule = summary.요일별스케줄[dayNames[today]];
    
    if (todaySchedule) {
        todaySchedule.forEach(schedule => {
            console.log(`• ${schedule.시작시간} (${schedule.지속시간}): ${schedule.상인들.join(', ')}`);
        });
    }
    
    return summary;
}

module.exports = { MerchantParser, displayMerchantInfo };
