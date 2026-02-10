import { useEffect, useState, useRef } from 'react';
import type { TestType, SeverityLevel } from '../types';

interface GaugeChartProps {
  value: number;
  testType?: TestType;
  unit: string;
  label: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showAnimation?: boolean;
  showZones?: boolean;
  variant?: 'default' | 'minimal' | 'detailed';
}

interface ThresholdConfig {
  min: number;
  max: number;
  low: number;
  normalMax: number;
  prediabetesMax: number;
}

const THRESHOLDS: Record<TestType, ThresholdConfig> = {
  fasting: { min: 40, max: 200, low: 70, normalMax: 99, prediabetesMax: 125 },
  hba1c: { min: 3, max: 12, low: 4.0, normalMax: 5.6, prediabetesMax: 6.4 },
  ppbs: { min: 40, max: 300, low: 70, normalMax: 139, prediabetesMax: 199 },
  rbs: { min: 40, max: 300, low: 70, normalMax: 139, prediabetesMax: 199 },
  ogtt: { min: 40, max: 300, low: 70, normalMax: 139, prediabetesMax: 199 },
};

const SIZE_CONFIG = {
  sm: { width: 120, height: 70, strokeWidth: 8, fontSize: 20, labelSize: 11, padding: 4 },
  md: { width: 160, height: 90, strokeWidth: 10, fontSize: 28, labelSize: 12, padding: 6 },
  lg: { width: 200, height: 110, strokeWidth: 12, fontSize: 36, labelSize: 13, padding: 8 },
  xl: { width: 260, height: 140, strokeWidth: 14, fontSize: 48, labelSize: 14, padding: 10 },
};

const COLORS = {
  low: {
    primary: '#10B981',
    secondary: '#34D399',
    glow: 'rgba(16, 185, 129, 0.3)',
    bg: '#ECFDF5',
  },
  moderate: {
    primary: '#F59E0B',
    secondary: '#FBBF24',
    glow: 'rgba(245, 158, 11, 0.3)',
    bg: '#FFFBEB',
  },
  high: {
    primary: '#EF4444',
    secondary: '#F87171',
    glow: 'rgba(239, 68, 68, 0.3)',
    bg: '#FEF2F2',
  },
};

const GaugeChart = ({
  value,
  testType = 'fasting',
  unit,
  label,
  size = 'md',
  showAnimation = true,
  showZones = true,
  variant = 'default',
}: GaugeChartProps) => {
  const [animatedValue, setAnimatedValue] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const gaugeRef = useRef<HTMLDivElement>(null);
  const config = SIZE_CONFIG[size];
  const thresholds = THRESHOLDS[testType];

  // Intersection Observer for viewport detection
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.3 }
    );

    if (gaugeRef.current) {
      observer.observe(gaugeRef.current);
    }

    return () => observer.disconnect();
  }, []);

  // Smooth animation with easing
  useEffect(() => {
    if (!showAnimation || !isVisible) {
      setAnimatedValue(value);
      return;
    }

    const duration = 1200;
    const startTime = Date.now();
    const startValue = 0;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out exponential
      const eased = 1 - Math.pow(1 - progress, 4);
      setAnimatedValue(startValue + (value - startValue) * eased);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value, showAnimation, isVisible]);

  // Calculate percentage for gauge position
  const clampedValue = Math.max(thresholds.min, Math.min(thresholds.max, animatedValue));
  const percentage = ((clampedValue - thresholds.min) / (thresholds.max - thresholds.min)) * 100;

  // Determine severity and color
  const getSeverity = (): SeverityLevel => {
    if (value < thresholds.low) return 'moderate';
    if (value <= thresholds.normalMax) return 'low';
    if (value <= thresholds.prediabetesMax) return 'moderate';
    return 'high';
  };

  const severity = getSeverity();
  const colors = COLORS[severity];

  // SVG calculations
  const centerX = config.width / 2;
  const centerY = config.height + config.padding;
  const radius = config.width / 2 - config.strokeWidth - config.padding;

  // Create arc path
  const createArc = (startAngle: number, endAngle: number) => {
    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;
    const x1 = centerX + radius * Math.cos(startRad);
    const y1 = centerY + radius * Math.sin(startRad);
    const x2 = centerX + radius * Math.cos(endRad);
    const y2 = centerY + radius * Math.sin(endRad);
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
  };

  const getZoneAngle = (threshold: number) => {
    const pct = ((threshold - thresholds.min) / (thresholds.max - thresholds.min)) * 100;
    return 180 + (pct / 100) * 180;
  };

  const valueAngle = 180 + (percentage / 100) * 180;
  const uniqueId = `gauge-${testType}-${label.replace(/\s+/g, '-')}-${Math.random().toString(36).substr(2, 9)}`;

  // Indicator position
  const indicatorX = centerX + (radius + 2) * Math.cos((valueAngle * Math.PI) / 180);
  const indicatorY = centerY + (radius + 2) * Math.sin((valueAngle * Math.PI) / 180);

  return (
    <div ref={gaugeRef} className="flex flex-col items-center">
      <div className="relative">
        <svg
          width={config.width}
          height={config.height + config.padding * 2}
          className="overflow-visible"
          style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.04))' }}
        >
          <defs>
            {/* Main gradient */}
            <linearGradient id={`${uniqueId}-gradient`} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={colors.secondary} />
              <stop offset="100%" stopColor={colors.primary} />
            </linearGradient>

            {/* Glow filter */}
            <filter id={`${uniqueId}-glow`} x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Drop shadow */}
            <filter id={`${uniqueId}-shadow`} x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="1" stdDeviation="2" floodOpacity="0.1" />
            </filter>
          </defs>

          {/* Background track */}
          <path
            d={createArc(180, 360)}
            fill="none"
            stroke="#E2E8F0"
            strokeWidth={config.strokeWidth}
            strokeLinecap="round"
            opacity="0.8"
          />

          {/* Zone indicators (subtle) */}
          {showZones && variant !== 'minimal' && (
            <g opacity="0.15">
              <path
                d={createArc(getZoneAngle(thresholds.low), getZoneAngle(thresholds.normalMax))}
                fill="none"
                stroke="#10B981"
                strokeWidth={config.strokeWidth - 2}
                strokeLinecap="round"
              />
              <path
                d={createArc(getZoneAngle(thresholds.normalMax), getZoneAngle(thresholds.prediabetesMax))}
                fill="none"
                stroke="#F59E0B"
                strokeWidth={config.strokeWidth - 2}
                strokeLinecap="round"
              />
              <path
                d={createArc(getZoneAngle(thresholds.prediabetesMax), 360)}
                fill="none"
                stroke="#EF4444"
                strokeWidth={config.strokeWidth - 2}
                strokeLinecap="round"
              />
            </g>
          )}

          {/* Value arc with gradient and glow */}
          {percentage > 0 && (
            <path
              d={createArc(180, valueAngle)}
              fill="none"
              stroke={`url(#${uniqueId}-gradient)`}
              strokeWidth={config.strokeWidth}
              strokeLinecap="round"
              filter={`url(#${uniqueId}-glow)`}
              style={{
                transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
            />
          )}

          {/* Indicator dot */}
          {percentage > 0 && (
            <g filter={`url(#${uniqueId}-shadow)`}>
              <circle
                cx={indicatorX}
                cy={indicatorY}
                r={config.strokeWidth / 2 + 3}
                fill="white"
              />
              <circle
                cx={indicatorX}
                cy={indicatorY}
                r={config.strokeWidth / 2}
                fill={colors.primary}
              />
            </g>
          )}
        </svg>

        {/* Center value display */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end"
          style={{ paddingBottom: config.padding + 4 }}
        >
          <div className="text-center">
            <span
              className="font-bold tracking-tight"
              style={{
                fontSize: config.fontSize,
                color: colors.primary,
                textShadow: `0 0 20px ${colors.glow}`,
              }}
            >
              {animatedValue.toFixed(testType === 'hba1c' ? 1 : 0)}
            </span>
            <span
              className="ml-1 font-medium text-slate-400"
              style={{ fontSize: config.labelSize }}
            >
              {unit}
            </span>
          </div>
        </div>
      </div>

      {/* Label */}
      <p
        className="mt-2 font-medium text-slate-600 text-center"
        style={{ fontSize: config.labelSize }}
      >
        {label}
      </p>

      {/* Optional: Range indicator for detailed variant */}
      {variant === 'detailed' && (
        <div className="flex items-center gap-3 mt-3">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-xs text-slate-500">Normal</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-amber-500" />
            <span className="text-xs text-slate-500">Elevated</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-rose-500" />
            <span className="text-xs text-slate-500">High</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default GaugeChart;
