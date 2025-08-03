<template>
  <div class="special-data-container">
    <!-- 页面标题横幅 -->
    <div class="page-banner glass-effect glow-effect">
      <div class="banner-content">
        <div class="banner-left">
          <h1 class="page-title text-gradient">
            <StarIcon class="icon-size"></StarIcon>
            特色数据中心
          </h1>
          <p class="page-subtitle">专业的市场数据分析与洞察</p>
          <p class="page-description">汇聚独特的市场数据指标，为您的投资决策提供专业支持</p>
        </div>
        <div class="banner-right">
          <div class="feature-highlights">
            <div class="highlight-item">
              <div class="highlight-icon">
                <ChartBarIcon class="icon-size" />
              </div>
              <div class="highlight-info">
                <div class="highlight-label">数据源</div>
                <div class="highlight-value">多维度</div>
              </div>
            </div>
            <div class="highlight-item">
              <div class="highlight-icon">
                <ClockIcon class="icon-size" />
              </div>
              <div class="highlight-info">
                <div class="highlight-label">更新频率</div>
                <div class="highlight-value">实时</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据模块区域 -->
    <div class="data-modules-section">
      <!-- SHIBOR利率数据面板 -->
      <div class="module-container">
        <ShiborDataPanel />
      </div>
      
      <!-- 申万指数分析面板 -->
      <div class="module-container">
        <SwanIndicesPanel_Fixed />
      </div>
      
      <!-- ETF指数分析面板 -->
      <div class="module-container">
        <ETFDailyPanel_Fixed />
      </div>
      
      <!-- 期权数据面板 -->
      <div class="module-container">
        <OptionsDataPanel />
      </div>
      
      <!-- 涨停板块分析面板 -->
      <div class="module-container">
        <LimitAnalysisPanel />
      </div>
      
      <!-- 两市融资融券分析面板 -->
      <div class="module-container">
        <MarketMarginAnalysisPanel />
      </div>
      
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  StarIcon,
  ChartBarIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline'
import ShiborDataPanel from '../components/ShiborDataPanel.vue'
import SwanIndicesPanel_Fixed from '../components/SwanIndicesPanel_Fixed.vue'
import ETFDailyPanel_Fixed from '../components/ETFDailyPanel_Fixed.vue'
import OptionsDataPanel from '../components/OptionsDataPanel.vue'
import LimitAnalysisPanel from '../components/LimitAnalysisPanel.vue'
import MarketMarginAnalysisPanel from '../components/MarketMarginAnalysisPanel.vue'

// 页面初始化
onMounted(() => {
  // 页面加载完成后的初始化逻辑
})
</script>

<style scoped>
.special-data-container {
  padding: var(--spacing-lg);
  min-height: 100vh;
  background: var(--gradient-primary);
}

/* 页面横幅样式 */
.page-banner {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-md);
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-xl);
}

.banner-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 var(--spacing-sm) 0;
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 1.25rem;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-xs) 0;
}

.page-description {
  font-size: 1rem;
  color: var(--text-tertiary);
  margin: 0;
}

.banner-right {
  flex-shrink: 0;
}

.feature-highlights {
  display: flex;
  gap: var(--spacing-lg);
}

.highlight-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
}

.highlight-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-accent);
  border-radius: var(--radius-sm);
  color: white;
}

.highlight-info {
  display: flex;
  flex-direction: column;
}

.highlight-label {
  font-size: 0.875rem;
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-xs);
}

.highlight-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* 模块网格样式 */
.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.module-card {
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-primary);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.module-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-accent);
}

.module-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.module-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-accent);
  border-radius: var(--radius-md);
  color: white;
}

.module-icon-size {
  width: 24px;
  height: 24px;
}

.module-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.module-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.module-description {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.module-status {
  display: inline-flex;
  align-items: center;
  padding: 6px var(--spacing-sm);
  background: var(--bg-tertiary);
  color: var(--accent-primary);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
  width: fit-content;
  border: 1px solid var(--border-accent);
}

/* 数据模块区域样式 */
.data-modules-section {
  margin-top: var(--spacing-xl);
}

.section-header {
  margin-bottom: var(--spacing-lg);
  text-align: center;
}

.section-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.section-subtitle {
  font-size: 1rem;
  color: var(--text-tertiary);
  margin: 0;
}

.module-container {
  margin-bottom: var(--spacing-xl);
}

.future-modules {
  margin-top: var(--spacing-xl);
}

.module-placeholder {
  padding: var(--spacing-2xl);
  border-radius: var(--radius-lg);
  background: var(--bg-secondary);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--spacing-lg);
}

.placeholder-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-accent);
  border-radius: var(--radius-xl);
  color: white;
}

.placeholder-icon-size {
  width: 40px;
  height: 40px;
}

.placeholder-text h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.placeholder-text p {
  font-size: 1rem;
  color: var(--text-tertiary);
  line-height: 1.6;
  margin: 0 0 var(--spacing-xs) 0;
}

.placeholder-text p:last-child {
  margin-bottom: 0;
}

/* 图标尺寸 */
.icon-size {
  width: 24px;
  height: 24px;
}

/* 玻璃效果和发光效果 */
.glass-effect {
  background: var(--bg-secondary);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-primary);
}

.glow-effect {
  position: relative;
  overflow: hidden;
}

.glow-effect::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, var(--border-secondary), transparent);
  transition: left var(--transition-slow);
}

.glow-effect:hover::before {
  left: 100%;
}

.text-gradient {
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.card {
  background: var(--bg-secondary);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .special-data-container {
    padding: var(--spacing-md);
  }
  
  .banner-content {
    flex-direction: column;
    text-align: center;
  }
  
  .feature-highlights {
    flex-direction: column;
    width: 100%;
  }
  
  .modules-grid {
    grid-template-columns: 1fr;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .module-placeholder {
    padding: var(--spacing-lg);
  }
}
</style>