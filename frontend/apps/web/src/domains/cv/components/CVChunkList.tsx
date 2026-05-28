import { useTranslation } from '@applark/i18n';
import { Separator } from '@applark/ui';

import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';
import { CVChunkType } from '@/domains/api/generated/model/cVChunkType';

const CHUNK_TYPE_ORDER: readonly CVChunkType[] = [
  CVChunkType.summary,
  CVChunkType.experience,
  CVChunkType.education,
  CVChunkType.project,
  CVChunkType.skill,
  CVChunkType.language,
  CVChunkType.other,
];

function ExperienceMeta({ metadata }: { metadata: Record<string, unknown> }) {
  const { t } = useTranslation();
  const company = metadata.company as string | undefined;
  const role = metadata.role as string | undefined;
  const start = metadata.start_date as string | undefined;
  const end = metadata.end_date as string | undefined;
  if (!company && !role && !start && !end) return null;
  return (
    <div className="text-body-default text-muted-foreground">
      {role && <span className="font-medium text-foreground">{role}</span>}
      {role && company && ' · '}
      {company && <span>{company}</span>}
      {(start || end) && (
        <span className="ml-2">
          ({start ?? '?'} – {end ?? t('cv.chunks.present')})
        </span>
      )}
    </div>
  );
}

function ProjectMeta({ metadata }: { metadata: Record<string, unknown> }) {
  const name = metadata.name as string | undefined;
  const techs = metadata.technologies as string[] | undefined;
  if (!name && !techs?.length) return null;
  return (
    <div className="text-body-default text-muted-foreground">
      {name && <span className="font-medium text-foreground">{name}</span>}
      {techs && techs.length > 0 && <span className="ml-2">[{techs.join(', ')}]</span>}
    </div>
  );
}

export function CVChunkList({ chunks }: { chunks: CVChunkRead[] }) {
  const { t } = useTranslation();
  if (chunks.length === 0) return null;

  const byType = new Map<CVChunkType, CVChunkRead[]>();
  for (const c of chunks) {
    const list = byType.get(c.chunk_type) ?? [];
    list.push(c);
    byType.set(c.chunk_type, list);
  }

  const visibleTypes = CHUNK_TYPE_ORDER.filter((t) => byType.has(t));

  return (
    <div className="flex flex-col gap-4 pt-2">
      {visibleTypes.map((type, idx) => (
        <div key={type} className="space-y-3">
          {idx > 0 && <Separator />}
          <h3 className="text-body-default-bold text-muted-foreground uppercase tracking-wide">
            {t(`cv.chunkType.${type}`)}
          </h3>
          <ul className="space-y-3">
            {(byType.get(type) ?? []).map((chunk) => (
              <li key={chunk.id} className="space-y-1">
                {type === CVChunkType.experience && (
                  <ExperienceMeta metadata={chunk.metadata as Record<string, unknown>} />
                )}
                {type === CVChunkType.project && <ProjectMeta metadata={chunk.metadata as Record<string, unknown>} />}
                <p className="whitespace-pre-wrap text-body-default text-foreground">{chunk.content}</p>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
