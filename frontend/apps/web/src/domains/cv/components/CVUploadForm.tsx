import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import { Controller, useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import { useTranslation } from '@applark/i18n';
import {
  Button,
  Field,
  FieldError,
  FieldLabel,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@applark/ui';

import { getGetCvDocumentsQueryKey, useCreateCvDocument } from '@/domains/api/generated/cv/cv';
import { CVDocumentKind } from '@/domains/api/generated/model/cVDocumentKind';
import { IntakePaywall } from '@/domains/billing/components/IntakePaywall';
import { useSubscription } from '@/domains/billing/hooks/useSubscription';

/** AI CV parsing is a paid capability — free users get the paywall instead. */
export function CVUploadForm() {
  const { isSubscribed, isLoading } = useSubscription();
  if (isLoading) return null;
  if (!isSubscribed) return <IntakePaywall />;
  return <CVUploadFormFields />;
}

function CVUploadFormFields() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  // <input type="file"> is uncontrolled — bump the key after each successful
  // upload to force-remount it so the filename clears from the DOM.
  const [fileKey, setFileKey] = useState(0);

  const schema = z.object({
    file: z.instanceof(File, { message: t('cv.upload.errorPick') }),
    kind: z.enum(['cv', 'cover_letter']),
  });
  type Values = z.infer<typeof schema>;

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { kind: CVDocumentKind.cv },
  });

  const create = useCreateCvDocument({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: getGetCvDocumentsQueryKey() });
        toast.success(t('cv.upload.toastSuccess'));
        reset({ kind: CVDocumentKind.cv });
        setFileKey((k) => k + 1);
      },
      onError: () => {
        toast.error(t('cv.upload.errorFailed'));
      },
    },
  });

  return (
    <form
      onSubmit={handleSubmit(({ file, kind }) =>
        // orval types `file` as string (OpenAPI `format: binary`) but at runtime the
        // generated code drops it straight into FormData — passing the File works.
        create.mutate({ data: { file: file as unknown as string, kind } })
      )}
      className="flex flex-col gap-4 rounded-lg border border-border bg-card p-4"
      noValidate
    >
      <Controller
        name="file"
        control={control}
        render={({ field }) => (
          <Field data-invalid={!!errors.file}>
            <FieldLabel htmlFor="cv-file">{t('cv.upload.fileLabel')}</FieldLabel>
            <Input
              key={fileKey}
              id="cv-file"
              type="file"
              accept="application/pdf"
              onBlur={field.onBlur}
              onChange={(event) => field.onChange(event.target.files?.[0])}
            />
            {errors.file && <FieldError>{errors.file.message}</FieldError>}
          </Field>
        )}
      />
      <Controller
        name="kind"
        control={control}
        render={({ field }) => (
          <Field>
            <FieldLabel htmlFor="cv-kind">{t('cv.upload.kindLabel')}</FieldLabel>
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger id="cv-kind" className="w-56">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={CVDocumentKind.cv}>{t('cv.kind.cv')}</SelectItem>
                <SelectItem value={CVDocumentKind.cover_letter}>{t('cv.kind.cover_letter')}</SelectItem>
              </SelectContent>
            </Select>
          </Field>
        )}
      />
      <div>
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? t('cv.upload.uploading') : t('cv.upload.upload')}
        </Button>
      </div>
    </form>
  );
}
