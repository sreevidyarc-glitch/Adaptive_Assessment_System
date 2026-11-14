import React, { useState, useEffect } from 'react';
import { authApi } from '../../api/auth';
import {
  UploadCloud,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Sliders,
  Layers,
  Search,
  Filter,
  ArrowRight,
  BookOpen,
  Sparkles,
  HelpCircle
} from 'lucide-react';

export const CourseMaterialProcessor = ({ courseId, courseTitle }) => {
  const [file, setFile] = useState(null);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.35);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoadingExisting, setIsLoadingExisting] = useState(false);
  const [mappingData, setMappingData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Chunk Explorer Filters
  const [selectedModuleFilter, setSelectedModuleFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch existing mapping on mount or when courseId changes
  useEffect(() => {
    if (courseId) {
      loadExistingMapping(similarityThreshold);
    }
  }, [courseId]);

  const loadExistingMapping = async (threshold) => {
    setIsLoadingExisting(true);
    setErrorMessage('');
    try {
      const data = await authApi.getCourseMaterialMapping(courseId, threshold);
      setMappingData(data);
    } catch (err) {
      console.warn('No existing material or error loading mapping:', err);
    } finally {
      setIsLoadingExisting(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMessage('');
    }
  };

  const handleUploadAndProcess = async (e) => {
    e.preventDefault();
    if (!file) {
      setErrorMessage('Please select a PDF, DOCX, or TXT file to process.');
      return;
    }

    setIsProcessing(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const data = await authApi.uploadCourseMaterial(courseId, file, similarityThreshold);
      setMappingData(data);
      setSuccessMessage(`Successfully extracted and mapped ${data.total_chunks} chunks from "${data.filename}".`);
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to process course material. Please check file format.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleThresholdChange = (newThreshold) => {
    setSimilarityThreshold(newThreshold);
    // Re-evaluate mapping for existing chunks
    if (mappingData && mappingData.total_chunks > 0) {
      loadExistingMapping(newThreshold);
    }
  };

  // Modules list for filtering
  const availableModules = mappingData
    ? Array.from(new Set(mappingData.chunks.map((c) => c.module_name)))
    : [];

  const filteredChunks = mappingData?.chunks?.filter((c) => {
    const matchesModule = selectedModuleFilter === 'ALL' || c.module_name === selectedModuleFilter;
    const matchesSearch =
      searchQuery === '' ||
      c.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.mapped_objective_code && c.mapped_objective_code.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesModule && matchesSearch;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Upload & Configuration Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-5">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-purple-600" />
              Course Material Ingestion & Module-Level Chunking
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Target Course: <strong className="text-slate-800">{courseTitle}</strong> • Supports PDF, DOCX, and TXT
            </p>
          </div>

          <div className="flex items-center gap-2 bg-purple-50 text-purple-800 border border-purple-200 px-3 py-1.5 rounded-xl text-xs font-mono font-medium">
            <Sparkles className="w-4 h-4 text-purple-600 shrink-0" />
            <span>Stages 1 & 2 Algorithm Pipeline</span>
          </div>
        </div>

        {errorMessage && (
          <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="mb-4 p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleUploadAndProcess} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* File Selection Zone */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Upload Syllabus or Lecture Notes (PDF, DOCX, TXT)
              </label>
              <div className="border-2 border-dashed border-slate-200 hover:border-purple-400 rounded-xl p-5 text-center transition-colors bg-slate-50/50">
                <input
                  type="file"
                  id="course-file-input"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="course-file-input"
                  className="cursor-pointer flex flex-col items-center justify-center gap-2"
                >
                  <FileText className="w-8 h-8 text-purple-600" />
                  <span className="text-xs font-semibold text-purple-700 hover:underline">
                    {file ? file.name : 'Choose a file or drag & drop here'}
                  </span>
                  <span className="text-[11px] text-slate-400">
                    PDF, DOCX, or TXT up to 25MB
                  </span>
                </label>
              </div>
            </div>

            {/* Configurable Similarity Threshold Slider */}
            <div className="space-y-3 bg-slate-50 p-5 rounded-xl border border-slate-200/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Sliders className="w-4 h-4 text-purple-600" />
                    Cosine Similarity Threshold (&tau;<sub>sim</sub>)
                  </label>
                  <span className="text-xs font-mono font-bold bg-white px-2.5 py-1 rounded-md border border-slate-200 text-purple-700">
                    {similarityThreshold.toFixed(2)}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Chunks with max cosine similarity &ge; {similarityThreshold.toFixed(2)} will be assigned to that objective.
                  Objectives with 0 matching chunks will trigger a <strong>Coverage Gap</strong> alert.
                </p>
              </div>

              <div>
                <input
                  type="range"
                  min="0.10"
                  max="0.80"
                  step="0.05"
                  value={similarityThreshold}
                  onChange={(e) => handleThresholdChange(parseFloat(e.target.value))}
                  className="w-full accent-purple-600 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1">
                  <span>0.10 (Broad)</span>
                  <span>0.35 (Recommended)</span>
                  <span>0.80 (Strict)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={isProcessing || !file}
              className="inline-flex items-center gap-2 bg-purple-700 hover:bg-purple-800 text-white font-semibold px-6 py-2.5 rounded-xl text-xs transition-all shadow-md disabled:opacity-50"
            >
              {isProcessing ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Chunking & Computing Similarities...
                </>
              ) : (
                <>
                  Process Material & Map Objectives
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Coverage Gaps Alert Banner (if any) */}
      {mappingData && mappingData.coverage_gaps && mappingData.coverage_gaps.length > 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <span>Coverage Gaps Detected ({mappingData.coverage_gaps.length} Objectives Unmapped)</span>
          </div>
          <p className="text-xs text-amber-800 leading-relaxed">
            The uploaded material contains no content chunks meeting the similarity threshold (&tau;<sub>sim</sub> = {similarityThreshold.toFixed(2)})
            for the following objectives. Consider uploading supplementary reading or lowering the threshold.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
            {mappingData.coverage_gaps.map((gap) => (
              <div
                key={gap.objective_id}
                className="bg-white p-3 rounded-xl border border-amber-200 text-xs shadow-sm"
              >
                <div className="font-mono font-bold text-amber-900 mb-1">
                  {gap.code}
                </div>
                <div className="text-slate-600 line-clamp-2">
                  {gap.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Learning Objectives Coverage Cards */}
      {mappingData && mappingData.objective_summaries && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-purple-600" />
              Curriculum Objectives Coverage Summary
            </h3>
            <span className="text-xs text-slate-500 font-mono">
              Total Chunks: {mappingData.total_chunks}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {mappingData.objective_summaries.map((obj) => (
              <div
                key={obj.objective_id}
                className={`bg-white rounded-xl border p-4 shadow-sm transition-all ${
                  obj.is_gap
                    ? 'border-amber-200 bg-amber-50/20'
                    : 'border-slate-200 hover:border-purple-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono font-bold text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                    {obj.code}
                  </span>
                  {obj.is_gap ? (
                    <span className="text-[11px] font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                      Coverage Gap
                    </span>
                  ) : (
                    <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                      {obj.mapped_chunk_count} Mapped Chunks
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-700 leading-snug mb-3 line-clamp-2">
                  {obj.description}
                </p>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Max Similarity:</span>
                  <span className="font-mono font-bold text-slate-900">
                    {Math.round(obj.max_similarity * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interactive Chunks Explorer */}
      {mappingData && mappingData.chunks && mappingData.chunks.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-600" />
                Extracted Module Chunks Explorer ({filteredChunks.length} of {mappingData.total_chunks})
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Inspect how text chunks from {mappingData.filename} are partitioned by module and mapped to objectives.
              </p>
            </div>

            {/* Filter controls */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter text..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-purple-500"
                />
              </div>

              <select
                value={selectedModuleFilter}
                onChange={(e) => setSelectedModuleFilter(e.target.value)}
                className="py-1.5 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-1 focus:ring-purple-500"
              >
                <option value="ALL">All Modules</option>
                {availableModules.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Chunks List */}
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {filteredChunks.map((chunk) => (
              <div
                key={chunk.id || chunk.chunk_index}
                className="bg-slate-50/70 rounded-xl border border-slate-200 p-4 text-xs space-y-2 hover:bg-white hover:border-purple-300 transition-all shadow-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800 bg-white border border-slate-200 px-2 py-0.5 rounded">
                      {chunk.module_name}
                    </span>
                    <span className="text-slate-400 font-mono">
                      Chunk #{chunk.chunk_index + 1}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {chunk.is_mapped ? (
                      <>
                        <span className="font-mono font-bold bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                          {chunk.mapped_objective_code}
                        </span>
                        <span className="font-mono font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded">
                          Sim: {Math.round((chunk.similarity_score || 0) * 100)}%
                        </span>
                      </>
                    ) : (
                      <span className="text-slate-500 bg-slate-200/80 px-2 py-0.5 rounded font-medium">
                        Sub-Threshold ({Math.round((chunk.similarity_score || 0) * 100)}% &lt; {Math.round(similarityThreshold * 100)}%)
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-slate-700 leading-relaxed">
                  {chunk.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

