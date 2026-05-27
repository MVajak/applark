import { type FormEvent, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { Button, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@postpilot/ui';

import { getGetCvDocumentsQueryKey, useCreateCvDocument } from '@/domains/api/generated/cv/cv';
import { CVDocumentKind } from '@/domains/api/generated/model/cVDocumentKind';
export function CVUploadForm() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState<CVDocumentKind>(CVDocumentKind.cv);
  const [fileKey, setFileKey] = useState(0);

  const create = useCreateCvDocument({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: getGetCvDocumentsQueryKey() });
        toast.success('CV uploaded — extracting chunks…');
        setFile(null);
        setFileKey((k) => k + 1);
      },
      onError: () => {
        toast.error('Upload failed');
      },
    },
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      toast.error('Pick a PDF first');
      return;
    }
    // orval types `file` as string (OpenAPI `format: binary`) but at runtime the
    // generated code drops it straight into FormData — passing the File works.
    create.mutate({ data: { file: file as unknown as string, kind } });
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4 rounded-lg border border-border bg-card p-4">
      <div className="grid gap-2">
        <Label htmlFor="cv-file">PDF file</Label>
        <Input
          key={fileKey}
          id="cv-file"
          type="file"
          accept="application/pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="cv-kind">Document kind</Label>
        <Select value={kind} onValueChange={(v) => setKind(v as CVDocumentKind)}>
          <SelectTrigger id="cv-kind" className="w-56">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={CVDocumentKind.cv}>CV</SelectItem>
            <SelectItem value={CVDocumentKind.cover_letter}>Cover Letter</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Button type="submit" disabled={!file || create.isPending}>
          {create.isPending ? 'Uploading…' : 'Upload'}
        </Button>
      </div>
    </form>
  );
}
