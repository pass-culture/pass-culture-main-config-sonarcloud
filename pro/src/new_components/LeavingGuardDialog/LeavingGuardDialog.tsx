import React from 'react'

import { ReactComponent as InfoIcon } from 'icons/info.svg'
import { Title } from 'ui-kit'

import styles from './LeavingGuardDialog.module.scss'

interface LeavingGuardDialogProps {
  title: string
  message: string
}

const LeavingGuardDialog = ({
  title,
  message,
}: LeavingGuardDialogProps): JSX.Element => {
  return (
    <div className={styles['dialog']}>
      <InfoIcon className={styles['dialog-icon']} />
      <Title level={3}>{title}</Title>
      <p className={styles['dialog-text']}>{message}</p>
    </div>
  )
}

export default LeavingGuardDialog
