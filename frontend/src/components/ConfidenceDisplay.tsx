import { useEffect, useState, useRef } from 'react';
import { Target, Info } from 'lucide-react';
import type { ConfidenceInterval } from '../types';

interface ConfidenceDisplayProps {
  interval: ConfidenceInterval;
  riskCategory: 'Low' | 'Moderate' | 'High';
}

const CATEGORY_COLORS = {
  Low: { bar: '#10B981', bg: 'from-emerald-500 to-teal-500' },
  Moderate: { bar: '#F59E0B', bg: 'from-amber-500 to-orange-500' },
  High: { bar: '#EF4444', bg: 'from-rose-500 to-red-500' },
};

const ConfidenceDisplay = ({ interval, riskCategory }: ConfidenceDisplayProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setIsVisible(true);
      },
      { threshold: 0.1 }
    );
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  if (interval.error) return null;

  const colors = CATEGORY_COLORS[riskCategory];
  const meanPct = interval.mean * 100;
  const rangeWidth = interval.ci_upper_pct - interval.ci_lower_pct;

  return (
    <div
      ref={containerRef}
      className={`card-elevated p-5 transition-all duration-700 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-xl bg-linear-to-br from-cyan-100 to-cyan-50 flex items-center justify-center">
          <Target className="w-5 h-5 text-cyan-600" />
        </div>
        <div>
          <h4 className="font-semibold text-slate-800">Prediction Confidence</h4>
          <p className="text-xs text-slate-500">
            Uncertainty range from {interval.tree_count} decision trees
          </p>
        </div>
      </div>

      {/* Main range display */}
      <div className="mb-6">
        <div className="flex items-baseline justify-center gap-2 mb-4">
          <span className="text-3xl font-bold text-slate-800">
            {interval.ci_lower_pct.toFixed(0)}% &ndash; {interval.ci_upper_pct.toFixed(0)}%
          </span>
          <span className="text-sm text-slate-500">risk range</span>
        </div>

        {/* Visual bar */}
        <div className="relative h-8 bg-slate-100 rounded-full overflow-hidden">
          {/* Zone backgrounds */}
          <div
            className="absolute inset-y-0 left-0 bg-emerald-100"
            style={{ width: '30%' }}
          />
          <div
            className="absolute inset-y-0 bg-amber-100"
            style={{ left: '30%', width: '30%' }}
          />
          <div
            className="absolute inset-y-0 right-0 bg-rose-100"
            style={{ width: '40%' }}
          />

          {/* CI range highlight */}
          <div
            className={`absolute inset-y-0 bg-linear-to-r ${colors.bg} rounded-full transition-all duration-1000 ease-out`}
            style={{
              left: isVisible ? `${interval.ci_lower_pct}%` : '50%',
              width: isVisible ? `${Math.max(rangeWidth, 1)}%` : '0%',
              opacity: 0.7,
            }}
          />

          {/* Mean marker */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-slate-800 transition-all duration-1000 ease-out"
            style={{
              left: isVisible ? `${meanPct}%` : '50%',
            }}
          >
            <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-slate-800 border-2 border-white shadow" />
          </div>

          {/* Zone labels */}
          <span className="absolute inset-y-0 left-[10%] flex items-center text-xs font-medium text-emerald-600/70">
            Low
          </span>
          <span className="absolute inset-y-0 left-[40%] flex items-center text-xs font-medium text-amber-600/70">
            Moderate
          </span>
          <span className="absolute inset-y-0 right-[12%] flex items-center text-xs font-medium text-rose-600/70">
            High
          </span>
        </div>

        {/* Scale markers */}
        <div className="flex justify-between mt-1 px-0.5 text-xs text-slate-400">
          <span>0%</span>
          <span>30%</span>
          <span>60%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100 text-center">
          <p className="text-label mb-0.5">Lower Bound</p>
          <p className="text-lg font-bold text-slate-800">{interval.ci_lower_pct.toFixed(1)}%</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100 text-center">
          <p className="text-label mb-0.5">Mean Estimate</p>
          <p className="text-lg font-bold" style={{ color: colors.bar }}>
            {meanPct.toFixed(1)}%
          </p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100 text-center">
          <p className="text-label mb-0.5">Upper Bound</p>
          <p className="text-lg font-bold text-slate-800">{interval.ci_upper_pct.toFixed(1)}%</p>
        </div>
      </div>

      {/* Explanation note */}
      <div className="mt-4 flex items-start gap-2 text-sm text-slate-500">
        <Info className="w-4 h-4 shrink-0 mt-0.5" />
        <p>
          This range shows how much the {interval.tree_count} individual decision trees
          in the model agree on your risk score. A narrower range means higher certainty.
        </p>
      </div>
    </div>
  );
};

export default ConfidenceDisplay;
