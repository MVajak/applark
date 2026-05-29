import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

import { useFormat } from '@applark/format';
import { useTranslation } from '@applark/i18n';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@applark/ui';

import { getGetCvDocumentsQueryKey, useDeleteCvDocument } from '@/domains/api/generated/cv/cv';
import type { CVDocumentRead } from '@/domains/api/generated/model/cVDocumentRead';
import { CVChunkList } from '@/domains/cv/components/CVChunkList';

export function CVDocumentCard({ document }: { document: CVDocumentRead }) {
  const { t } = useTranslation();
  const fmt = useFormat();
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const isProcessing = document.chunks.length === 0;

  const remove = useDeleteCvDocument({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: getGetCvDocumentsQueryKey() });
        toast.success(t('cv.card.toastDeleted'));
      },
      onError: () => toast.error(t('cv.card.toastDeleteFailed')),
    },
  });

  return (
    <Card className="p-5">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-1.5">
            <CardTitle className="truncate text-title-small-bold">{document.filename}</CardTitle>
            <div className="flex items-center gap-2 text-body-small text-muted-foreground">
              <Badge variant="secondary">{t(`cv.kind.${document.kind}`)}</Badge>
              <span>{fmt.relativeTime(document.created_at)}</span>
              {isProcessing && (
                <Badge variant="outline" className="animate-pulse">
                  {t('cv.card.processing')}
                </Badge>
              )}
              {!isProcessing && <span>· {t('cv.card.chunks', { count: document.chunks.length })}</span>}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded((v) => !v)}
              disabled={isProcessing}
              aria-label={expanded ? t('cv.card.collapse') : t('cv.card.expand')}
            >
              {expanded ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="sm" aria-label={t('cv.card.deleteAria')} disabled={remove.isPending}>
                  <Trash2 className="size-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>{t('cv.card.deleteTitle')}</AlertDialogTitle>
                  <AlertDialogDescription>
                    {t('cv.card.deleteDescription', { filename: document.filename })}
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
                  <AlertDialogAction onClick={() => remove.mutate({ documentId: document.id })}>
                    {t('common.delete')}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardHeader>
      {expanded && !isProcessing && (
        <CardContent>
          <CVChunkList chunks={document.chunks} />
        </CardContent>
      )}
    </Card>
  );
}
