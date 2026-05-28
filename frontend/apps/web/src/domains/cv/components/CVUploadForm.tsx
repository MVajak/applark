import { type FormEvent, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { useTranslation } from '@applark/i18n';
import { Button, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@applark/ui';

import { getGetCvDocumentsQueryKey, useCreateCvDocument } from '@/domains/api/generated/cv/cv';
import { CVDocumentKind } from '@/domains/api/generated/model/cVDocumentKind';
export function CVUploadForm() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState<CVDocumentKind>(CVDocumentKind.cv);
  const [fileKey, setFileKey] = useState(0);

  const create = useCreateCvDocument({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: getGetCvDocumentsQueryKey() });
        toast.success(t('cv.upload.toastSuccess'));
        setFile(null);
        setFileKey((k) => k + 1);
      },
      onError: () => {
        toast.error(t('cv.upload.errorFailed'));
      },
    },
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      toast.error(t('cv.upload.errorPick'));
      return;
    }
    // orval types `file` as string (OpenAPI `format: binary`) but at runtime the
    // generated code drops it straight into FormData — passing the File works.
    create.mutate({ data: { file: file as unknown as string, kind } });
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4 rounded-lg border border-border bg-card p-4">
      <div className="grid gap-2">
        <Label htmlFor="cv-file">{t('cv.upload.fileLabel')}</Label>
        <Input
          key={fileKey}
          id="cv-file"
          type="file"
          accept="application/pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="cv-kind">{t('cv.upload.kindLabel')}</Label>
        <Select value={kind} onValueChange={(v) => setKind(v as CVDocumentKind)}>
          <SelectTrigger id="cv-kind" className="w-56">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={CVDocumentKind.cv}>{t('cv.kind.cv')}</SelectItem>
            <SelectItem value={CVDocumentKind.cover_letter}>{t('cv.kind.cover_letter')}</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Button type="submit" disabled={!file || create.isPending}>
          {create.isPending ? t('cv.upload.uploading') : t('cv.upload.upload')}
        </Button>
      </div>
    </form>
  );
}
