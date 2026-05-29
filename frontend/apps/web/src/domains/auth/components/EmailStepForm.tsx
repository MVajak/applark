import { zodResolver } from '@hookform/resolvers/zod';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';

import { useTranslation } from '@applark/i18n';
import { Button, Field, FieldError, FieldLabel, Input } from '@applark/ui';

export function EmailStepForm({
  onSubmit,
  isSubmitting,
}: {
  onSubmit: (email: string) => void;
  isSubmitting: boolean;
}) {
  const { t } = useTranslation();
  const schema = z.object({ email: z.email({ message: t('auth.emailInvalid') }) });
  type Values = z.infer<typeof schema>;

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { email: '' },
    mode: 'onBlur',
  });

  return (
    <form onSubmit={handleSubmit(({ email }) => onSubmit(email))} className="flex flex-col gap-4" noValidate>
      <Controller
        name="email"
        control={control}
        render={({ field }) => (
          <Field data-invalid={!!errors.email}>
            <FieldLabel htmlFor="login-email">{t('auth.emailLabel')}</FieldLabel>
            <Input
              id="login-email"
              type="email"
              autoComplete="email"
              autoFocus
              placeholder={t('auth.emailPlaceholder')}
              aria-invalid={!!errors.email}
              {...field}
            />
            {errors.email && <FieldError>{errors.email.message}</FieldError>}
          </Field>
        )}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t('auth.sending') : t('auth.sendCode')}
      </Button>
    </form>
  );
}
