import type { Story } from '@storybook/react'
import React from 'react'

import InfoBox, { IInfoBoxProps } from './InfoBox'

export default {
  title: 'ui-kit/InfoBox',
  component: InfoBox,
}

const Template: Story<IInfoBoxProps> = props => (
  <div style={{ maxWidth: '316px' }}>
    <InfoBox {...props} />
  </div>
)

export const InfoWithLink = Template.bind({})
InfoWithLink.args = {
  type: 'info',
  link: { text: 'Suivre le lien', to: '#', isExternal: true },
  text: 'Molestie fermentum accumsan at faucibus leo massa proin. Suspendisse sed sed fringilla ipsum adipiscing.',
}

export const ImportantWithLink = Template.bind({})
ImportantWithLink.args = {
  type: 'important',
  link: { text: 'Suivre le lien', to: '#', isExternal: true },
  text: 'Molestie fermentum accumsan at faucibus leo massa proin. Suspendisse sed sed fringilla ipsum adipiscing.',
}
