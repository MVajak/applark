import { FileText } from 'lucide-react';

import { useTranslation } from '@applark/i18n';
import { Skeleton } from '@applark/ui';

import { useGetCvDocuments } from '@/domains/api/generated/cv/cv';
import { CVDocumentCard } from '@/domains/cv/components/CVDocumentCard';
import { CVUploadForm } from '@/domains/cv/components/CVUploadForm';
import { EmptyState } from '@/domains/shell/components/EmptyState';

export function CVPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useGetCvDocuments();

  return (
    <div className="space-y-8">
      <header className="space-y-1 border-border/60 border-b pb-6">
        <h1 className="text-title-large-bold tracking-tight">{t('cv.title')}</h1>
        <p className="text-body-default text-muted-foreground">{t('cv.description')}</p>
      </header>

      <section className="space-y-3">
        <CVUploadForm />
      </section>

      <section className="space-y-3">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : data && data.length > 0 ? (
          <div className="space-y-3">
            {data.map((doc) => (
              <CVDocumentCard key={doc.id} document={doc} />
            ))}
          </div>
        ) : (
          <EmptyState icon={FileText} title={t('cv.empty.title')} description={t('cv.empty.description')} />
        )}
      </section>
    </div>
  );
}
