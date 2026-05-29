import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useTranslation } from '@applark/i18n';
import { Card } from '@applark/ui';

import { getErrorDetail } from '@/domains/api/client';
import { useRequestOtp, useVerifyOtp } from '@/domains/api/generated/auth/auth';
import { EmailStepForm } from '@/domains/auth/components/EmailStepForm';
import { OtpStepForm } from '@/domains/auth/components/OtpStepForm';
import { useAuthStore } from '@/domains/auth/store';
import { BrandMark } from '@/domains/shell/components/BrandMark';

export function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);

  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [email, setEmail] = useState('');

  const requestOtp = useRequestOtp({
    mutation: {
      onSuccess: (_data, variables) => {
        setEmail(variables.data.email);
        setStep('otp');
      },
      onError: (err) => toast.error(getErrorDetail(err) ?? t('auth.errorRequest')),
    },
  });

  const verifyOtp = useVerifyOtp({
    mutation: {
      onSuccess: (tokens) => {
        setTokens(tokens);
        navigate('/', { replace: true });
      },
      onError: (err) => toast.error(getErrorDetail(err) ?? t('auth.errorVerify')),
    },
  });

  return (
    <div className="flex min-h-dvh items-center justify-center px-4">
      <Card className="w-full max-w-sm gap-6 p-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <BrandMark variant="icon" className="size-10" />
          <div className="space-y-1">
            <h1 className="text-title-default-bold">{t('auth.title')}</h1>
            <p className="text-body-small text-muted-foreground">
              {step === 'email' ? t('auth.subtitle') : t('auth.otpSubtitle', { email })}
            </p>
          </div>
        </div>

        {step === 'email' ? (
          <EmailStepForm
            isSubmitting={requestOtp.isPending}
            onSubmit={(value) => requestOtp.mutate({ data: { email: value } })}
          />
        ) : (
          <OtpStepForm
            isVerifying={verifyOtp.isPending}
            onVerify={(code) => verifyOtp.mutate({ data: { email, code } })}
            onBack={() => setStep('email')}
          />
        )}
      </Card>
    </div>
  );
}
