import { useState } from 'react';
import { Sparkles } from 'lucide-react';

import { Button } from '@applark/ui';

import {
  getGetCoverLettersQueryKey,
  useGenerateCoverLetter,
  useGetCoverLetters,
} from '@/domains/api/generated/cover-letters/cover-letters';
import type { CoverLetterDraftRead } from '@/domains/api/generated/model/coverLetterDraftRead';
import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';
import { CoverLetterDraftCard } from '@/domains/cover_letters/components/CoverLetterDraftCard';
import type { FeatureSectionConfig } from '@/domains/jobs/components/FeatureSection';

function CoverLetterDrafts({ drafts, chunks }: { drafts: CoverLetterDraftRead[]; chunks: CVChunkRead[] }) {
  const [showPrevious, setShowPrevious] = useState(false);

  const chunkLookup = new Map<string, CVChunkRead>();
  for (const chunk of chunks) chunkLookup.set(chunk.id, chunk);

  const [latestDraft, ...previousDrafts] = drafts;
  if (!latestDraft) return null;

  return (
    <div className="space-y-4">
      <CoverLetterDraftCard draft={latestDraft} chunkLookup={chunkLookup} />

      {previousDrafts.length > 0 && (
        <div className="pt-2">
          <Button type="button" variant="ghost" size="sm" onClick={() => setShowPrevious((v) => !v)} className="-ml-2">
            {showPrevious ? 'Hide' : 'Show'} previous drafts ({previousDrafts.length})
          </Button>
          {showPrevious && (
            <div className="mt-3 space-y-4">
              {previousDrafts.map((d) => (
                <CoverLetterDraftCard key={d.id} draft={d} chunkLookup={chunkLookup} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export const coverLetterFeature: FeatureSectionConfig<CoverLetterDraftRead[]> = {
  icon: Sparkles,
  requiresMatch: true,
  useLatest: useGetCoverLetters,
  useMutation: useGenerateCoverLetter,
  invalidateKey: getGetCoverLettersQueryKey,
  hasResult: (data): data is CoverLetterDraftRead[] => (data?.length ?? 0) > 0,
  pendingCaption: 'Drafting…',
  copy: {
    ready: 'Draft a cover letter grounded in your match strengths.',
    cost: 'Uses Claude Sonnet — ~$0.02 per draft.',
    needsMatch: 'A cover letter draft cites your match strengths — run a match first so it references real CV chunks.',
    runLabel: 'Generate cover letter',
    rerunLabel: 'Generate again',
    success: 'Draft ready',
    errorFallback: 'Cover letter generation failed',
  },
  renderResult: ({ result, chunks }) => <CoverLetterDrafts drafts={result} chunks={chunks} />,
};
