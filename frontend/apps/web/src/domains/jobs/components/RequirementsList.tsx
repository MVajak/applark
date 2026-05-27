import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

import { Button, Card } from '@applark/ui';

import type { JobRequirementRead } from '@/domains/api/generated/model/jobRequirementRead';
import { RequirementCategory } from '@/domains/api/generated/model/requirementCategory';

const CATEGORY_ORDER: readonly RequirementCategory[] = [
  RequirementCategory.required,
  RequirementCategory.nice_to_have,
  RequirementCategory.responsibility,
];

const CATEGORY_LABEL: Record<RequirementCategory, string> = {
  required: 'Required',
  nice_to_have: 'Nice to have',
  responsibility: 'Responsibilities',
};

function RequirementGroup({
  label,
  items,
  defaultOpen,
}: {
  label: string;
  items: JobRequirementRead[];
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  if (items.length === 0) return null;
  return (
    <div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setOpen((v) => !v)}
        className="-ml-2 w-full justify-start gap-2"
      >
        {open ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground">({items.length})</span>
      </Button>
      {open && (
        <ul className="mt-1 ml-6 list-disc space-y-1.5 text-body-default text-foreground/90">
          {items.map((req) => (
            <li key={req.id} className="leading-snug">
              {req.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function RequirementsList({ requirements }: { requirements: JobRequirementRead[] }) {
  if (requirements.length === 0) {
    return <p className="text-body-default text-muted-foreground">No requirements extracted.</p>;
  }

  const grouped = new Map<RequirementCategory, JobRequirementRead[]>();
  for (const req of requirements) {
    const list = grouped.get(req.category) ?? [];
    list.push(req);
    grouped.set(req.category, list);
  }

  return (
    <Card className="space-y-3 p-4">
      {CATEGORY_ORDER.map((category) => (
        <RequirementGroup
          key={category}
          label={CATEGORY_LABEL[category]}
          items={grouped.get(category) ?? []}
          defaultOpen={category === RequirementCategory.required}
        />
      ))}
    </Card>
  );
}
