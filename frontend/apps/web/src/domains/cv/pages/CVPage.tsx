import { FileText } from 'lucide-react';

import { Skeleton } from '@postpilot/ui';

import { useGetCvDocuments } from '@/domains/api/generated/cv/cv';
import { CVDocumentCard } from '@/domains/cv/components/CVDocumentCard';
import { CVUploadForm } from '@/domains/cv/components/CVUploadForm';
import { EmptyState } from '@/domains/shell/components/EmptyState';

export function CVPage() {
  const { data, isLoading } = useGetCvDocuments();

  return (
    <div className="space-y-8">
      <header className="space-y-1 border-border/60 border-b pb-6">
        <h1 className="text-title-large-bold tracking-tight">Your CVs</h1>
        <p className="text-body-default text-muted-foreground">Upload and manage the CVs you compare against jobs.</p>
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
          <EmptyState
            icon={FileText}
            title="No CVs uploaded yet"
            description="Drop a PDF above to get started. Once it's parsed, PostPilot can match it against any job posting you add."
          />
        )}
      </section>
    </div>
  );
}
