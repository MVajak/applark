import { Card } from '@applark/ui';

export function MatchSummary({ summary }: { summary: string }) {
  return (
    <Card className="p-4">
      <p className="whitespace-pre-wrap text-body-default text-foreground/90">{summary}</p>
    </Card>
  );
}
