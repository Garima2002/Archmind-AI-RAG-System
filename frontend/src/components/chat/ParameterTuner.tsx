import React from 'react';
import { Sliders, RotateCcw, Info } from 'lucide-react';

interface ParameterTunerProps {
  topK: number;
  similarityThreshold: number;
  onTopKChange: (val: number) => void;
  onSimilarityThresholdChange: (val: number) => void;
  onReset: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

export const ParameterTuner: React.FC<ParameterTunerProps> = ({
  topK,
  similarityThreshold,
  onTopKChange,
  onSimilarityThresholdChange,
  onReset,
  isOpen,
  onToggle,
}) => {
  return (
    <div className="border border-white/10 rounded-xl bg-[#0f1420]/80 backdrop-blur-md overflow-hidden transition-all mb-4">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/60">
        <button
          onClick={onToggle}
          className="flex items-center gap-2 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
        >
          <Sliders className="w-3.5 h-3.5 text-indigo-400" />
          <span>Retrieval Parameters</span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            top_k={topK} | threshold={similarityThreshold.toFixed(2)}
          </span>
        </button>

        <div className="flex items-center gap-2">
          {(topK !== 4 || similarityThreshold !== 0.35) && (
            <button
              onClick={onReset}
              className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
            >
              <RotateCcw className="w-3 h-3" />
              Reset Defaults
            </button>
          )}
          <button
            onClick={onToggle}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            {isOpen ? 'Collapse' : 'Adjust'}
          </button>
        </div>
      </div>

      {/* Expandable Sliders */}
      {isOpen && (
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-5 border-t border-white/5 animate-fade-in">
          {/* Top K */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1.5">
              <label htmlFor="top-k-slider" className="font-medium text-slate-300 flex items-center gap-1">
                Top-K Retrieved Chunks:
                <span className="font-mono text-indigo-400 font-bold ml-1">{topK}</span>
              </label>
              <span className="text-[11px] text-slate-500 font-mono">1 – 20 (Default: 4)</span>
            </div>
            <input
              id="top-k-slider"
              type="range"
              min={1}
              max={20}
              step={1}
              value={topK}
              onChange={(e) => onTopKChange(parseInt(e.target.value, 10))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <p className="text-[11px] text-slate-400 mt-1.5 flex items-center gap-1 leading-normal">
              <Info className="w-3 h-3 text-slate-500 shrink-0" />
              Controls maximum documentation excerpts passed to the synthesizer.
            </p>
          </div>

          {/* Similarity Threshold */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1.5">
              <label htmlFor="similarity-threshold-slider" className="font-medium text-slate-300 flex items-center gap-1">
                Cosine Similarity Threshold:
                <span className="font-mono text-cyan-400 font-bold ml-1">
                  {similarityThreshold.toFixed(2)}
                </span>
              </label>
              <span className="text-[11px] text-slate-500 font-mono">0.00 – 1.00 (Default: 0.35)</span>
            </div>
            <input
              id="similarity-threshold-slider"
              type="range"
              min={0.0}
              max={0.9}
              step={0.05}
              value={similarityThreshold}
              onChange={(e) => onSimilarityThresholdChange(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
            <p className="text-[11px] text-slate-400 mt-1.5 flex items-center gap-1 leading-normal">
              <Info className="w-3 h-3 text-slate-500 shrink-0" />
              Minimum score required to use a chunk. Below this triggers fallback.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
