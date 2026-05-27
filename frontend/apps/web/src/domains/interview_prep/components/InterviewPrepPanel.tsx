import { Badge, Card } from '@postpilot/ui';

import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';
import type { InterviewPrepRunRead } from '@/domains/api/generated/model/interviewPrepRunRead';
import type { InterviewQuestion } from '@/domains/api/generated/model/interviewQuestion';
import { QuestionCategory } from '@/domains/api/generated/model/questionCategory';
import { QuestionCard } from '@/domains/interview_prep/components/QuestionCard';
import { QuestionsToAskBox } from '@/domains/interview_prep/components/QuestionsToAskBox';

const CATEGORY_ORDER: readonly QuestionCategory[] = [
  QuestionCategory.technical,
  QuestionCategory.system_design,
  QuestionCategory.role_specific,
  QuestionCategory.behavioral,
  QuestionCategory.culture_fit,
];

const CATEGORY_HEADING: Record<QuestionCategory, string> = {
  technical: 'Technical',
  system_design: 'System design',
  role_specific: 'Role-specific',
  behavioral: 'Behavioral',
  culture_fit: 'Culture fit',
};

export function InterviewPrepPanel({ run, chunks }: { run: InterviewPrepRunRead; chunks: CVChunkRead[] }) {
  const chunkLookup = new Map<string, CVChunkRead>();
  for (const chunk of chunks) chunkLookup.set(chunk.id, chunk);

  const byCategory = new Map<QuestionCategory, InterviewQuestion[]>();
  for (const q of run.questions) {
    const list = byCategory.get(q.category) ?? [];
    list.push(q);
    byCategory.set(q.category, list);
  }

  return (
    <div className="space-y-6">
      <Card className="bg-muted/30 p-5">
        <p className="whitespace-pre-wrap text-body-default">{run.role_overview}</p>
      </Card>

      {run.likely_areas_of_focus.length > 0 && (
        <div className="space-y-2">
          <p className="text-body-small text-muted-foreground uppercase tracking-wide">Likely areas of focus</p>
          <div className="flex flex-wrap gap-2">
            {run.likely_areas_of_focus.map((area, i) => (
              <Badge key={i} variant="secondary" className="font-normal">
                {area}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-6">
        {CATEGORY_ORDER.filter((cat) => (byCategory.get(cat) ?? []).length > 0).map((cat) => (
          <section key={cat} className="space-y-3">
            <h3 className="text-body-default-bold text-muted-foreground">{CATEGORY_HEADING[cat]}</h3>
            <div className="space-y-3">
              {(byCategory.get(cat) ?? []).map((q, i) => (
                <QuestionCard key={`${cat}-${i}`} question={q} chunkLookup={chunkLookup} />
              ))}
            </div>
          </section>
        ))}
      </div>

      <QuestionsToAskBox items={run.questions_to_ask_them} />
    </div>
  );
}
