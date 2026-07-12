import { useState } from 'react';
import { Modal } from '../common/Modal';
import { SystemCheck } from './SystemCheck';
import { ProfileSelector } from './ProfileSelector';
import { DownloadProgress } from './DownloadProgress';
import { BenchmarkComplete } from './BenchmarkComplete';

enum WizardStep {
  SYSTEM_CHECK,
  PROFILE_SELECT,
  DOWNLOAD,
  COMPLETE,
}

interface WizardModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function WizardModal({ isOpen, onClose }: WizardModalProps) {
  const [step, setStep] = useState<WizardStep>(WizardStep.SYSTEM_CHECK);

  const handleSystemCheckComplete = () => {
    setStep(WizardStep.PROFILE_SELECT);
  };

  const handleProfileSelect = () => {
    setStep(WizardStep.DOWNLOAD);
  };

  const handleDownloadComplete = () => {
    setStep(WizardStep.COMPLETE);
  };

  if (!isOpen) return null;

  return (
    <Modal title="Hearth Setup" isOpen={isOpen} onClose={onClose}>
      {step === WizardStep.SYSTEM_CHECK && <SystemCheck onComplete={handleSystemCheckComplete} />}
      {step === WizardStep.PROFILE_SELECT && <ProfileSelector onSelect={handleProfileSelect} />}
      {step === WizardStep.DOWNLOAD && (
        <DownloadProgress
          models={['nomic-embed-text-v1.5', 'llama-3.2-1b']}
          onComplete={handleDownloadComplete}
        />
      )}
      {step === WizardStep.COMPLETE && <BenchmarkComplete onClose={onClose} />}
    </Modal>
  );
}