import { useState } from 'react';

import { Button, Card, Skeleton } from '@postpilot/ui';

import { useGetCoverLetters } from '@/domains/api/generated/cover-letters/cover-letters';
import { useGetCvDocuments } from '@/domains/api/generated/cv/cv';
import { useGetLatestMatch } from '@/domains/api/generated/matching/matching';
import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';
import { CoverLetterDraftCard } from '@/domains/cover_letters/components/CoverLetterDraftCard';
import { GenerateCoverLetterButton } from '@/domains/cover_letters/components/GenerateCoverLetterButton';
import { DisabledButtonWithTooltip } from '@/domains/shell/components/DisabledButtonWithTooltip';

export function CoverLetterSection({ jobId }: { jobId: string }) {
  const [showPrevious, setShowPrevious] = useState(false);

  const matchQuery = useGetLatestMatch(jobId);
  const draftsQuery = useGetCoverLetters(jobId);
  const cvsQuery = useGetCvDocuments();

  const latestCv = cvsQuery.data?.[0];
  const chunkLookup = new Map<string, CVChunkRead>();
  if (latestCv) {
    for (const chunk of latestCv.chunks) chunkLookup.set(chunk.id, chunk);
  }

  const drafts = draftsQuery.data ?? [];
  const latestDraft = drafts[0];
  const previousDrafts = drafts.slice(1);

  const hasMatch = !!matchQuery.data;

  if (draftsQuery.isLoading || matchQuery.isLoading) return <Skeleton className="h-24 w-full" />;

  if (!latestDraft) {
    if (hasMatch) {
      return (
        <Card className="flex items-center justify-between gap-4 p-6">
          <div>
            <p className="text-body-default">Draft a cover letter grounded in your match strengths.</p>
            <p className="text-body-small text-muted-foreground">Uses Claude Sonnet — ~$0.02 per draft.</p>
          </div>
          <GenerateCoverLetterButton jobId={jobId} />
        </Card>
      );
    }
    return (
      <Card className="flex items-center justify-between gap-4 p-6">
        <div>
          <p className="text-body-default">A cover letter draft is grounded in your match strengths.</p>
          <p className="text-body-small text-muted-foreground">Run a match first so the letter cites real CV chunks.</p>
        </div>
        <DisabledButtonWithTooltip label="Generate cover letter" hint="Run match against your CV first" />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <CoverLetterDraftCard draft={latestDraft} chunkLookup={chunkLookup} />

      <div className="flex justify-end">
        <GenerateCoverLetterButton jobId={jobId} variant="outline" label="Generate again" />
      </div>

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
