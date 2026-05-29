import { zodResolver } from '@hookform/resolvers/zod';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';

import { useTranslation } from '@applark/i18n';
import { Button, Field, FieldError, InputOTP, InputOTPGroup, InputOTPSlot } from '@applark/ui';

export function OtpStepForm({
  onVerify,
  isVerifying,
  onBack,
}: {
  onVerify: (code: string) => void;
  isVerifying: boolean;
  onBack: () => void;
}) {
  const { t } = useTranslation();
  const schema = z.object({
    code: z.string().regex(/^\d{6}$/, { message: t('auth.codeInvalid') }),
  });
  type Values = z.infer<typeof schema>;

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { code: '' },
  });

  const submit = handleSubmit(({ code }) => onVerify(code));

  return (
    <form onSubmit={submit} className="flex flex-col items-center gap-4" noValidate>
      <Controller
        name="code"
        control={control}
        render={({ field }) => (
          <Field data-invalid={!!errors.code} className="items-center">
            <InputOTP
              maxLength={6}
              autoFocus
              disabled={isVerifying}
              containerClassName="justify-center"
              value={field.value}
              onChange={field.onChange}
              onBlur={field.onBlur}
              onComplete={submit}
            >
              <InputOTPGroup>
                <InputOTPSlot index={0} />
                <InputOTPSlot index={1} />
                <InputOTPSlot index={2} />
                <InputOTPSlot index={3} />
                <InputOTPSlot index={4} />
                <InputOTPSlot index={5} />
              </InputOTPGroup>
            </InputOTP>
            {errors.code && <FieldError className="text-center">{errors.code.message}</FieldError>}
          </Field>
        )}
      />
      <Button type="submit" disabled={isVerifying} className="w-full">
        {isVerifying ? t('auth.verifying') : t('auth.verify')}
      </Button>
      <Button type="button" variant="ghost" size="sm" onClick={onBack}>
        {t('auth.changeEmail')}
      </Button>
    </form>
  );
}
