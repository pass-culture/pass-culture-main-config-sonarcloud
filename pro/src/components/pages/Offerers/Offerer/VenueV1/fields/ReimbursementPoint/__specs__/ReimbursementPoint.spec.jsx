import '@testing-library/jest-dom'

import * as pcapi from 'repository/pcapi/pcapi'

import { render, screen, waitFor } from '@testing-library/react'
import { Form } from 'react-final-form'

import React from 'react'
import ReimbursementPoint from '../ReimbursementPoint'

jest.mock('repository/pcapi/pcapi', () => ({
  getBusinessUnits: jest.fn(),
}))

const renderReimbursementPoint = async props => {
  const rtlReturn = await render(
    <Form onSubmit={() => {}}>{() => <ReimbursementPoint {...props} />}</Form>
  )

  const loadingMessage = screen.queryByText('Chargement en cours ...')
  await waitFor(() => expect(loadingMessage).not.toBeInTheDocument())

  return rtlReturn
}

describe('src | Venue | ReimbursementPoint', () => {
  const venue = {
    id: 'AA',
    name: 'fake venue name',
  }
  const offerer = {
    id: 'BB',
    name: 'fake offerer name',
  }
  let props
  beforeEach(() => {
    props = { venue, offerer }
  })

  it('should display reimbursement point secion  when offerer has at least one', async () => {
    // Given
    pcapi.getBusinessUnits.mockResolvedValue([
      {
        name: 'Reimbursement Point #1',
        siret: '111222333',
        id: 1,
        bic: 'BDFEFRPP',
        iban: 'FR9410010000000000000000022',
      },
    ])

    // When
    await renderReimbursementPoint(props)

    // Then
    expect(
      screen.queryByText('Sélectionner des coordonnées dans la liste')
    ).toBeInTheDocument()
  })

  it('should display reimbursement point with the correct name ', async () => {
    // Given
    pcapi.getBusinessUnits.mockResolvedValue([
      {
        name: 'Reimbursement Point #1',
        siret: '111222333',
        id: 1,
        bic: 'BDFEFRPP',
        iban: 'FR9410010000000000000000022',
      },
    ])

    // When
    await renderReimbursementPoint(props)

    // Then
    expect(
      screen.queryByText('111 222 333 - FR9410010000000000000000022')
    ).toBeInTheDocument()
  })

  it('should not display reimbursement point selection  when offerer has not one', async () => {
    // Given
    pcapi.getBusinessUnits.mockResolvedValue([])

    // When
    await renderReimbursementPoint(props)

    // Then
    expect(
      screen.queryByText('Sélectionner des coordonnées dans la liste')
    ).not.toBeInTheDocument()
  })

  it('should display add cb button when venue does not have reimbursement point', async () => {
    // Given
    pcapi.getBusinessUnits.mockResolvedValue([])

    // When
    await renderReimbursementPoint(props)

    // Then
    expect(
      screen.getByRole('button', {
        name: 'Ajouter des coordonnées bancaires',
      })
    ).toBeInTheDocument()
  })

  it('should display modify button when venue has already add dms cb', async () => {
    // Given
    const venueWithCb = {
      id: 'AA',
      name: 'fake venue name',
      isBusinessUnitMainVenue: true,
    }

    props.venue = venueWithCb
    pcapi.getBusinessUnits.mockResolvedValue([
      {
        name: 'Reimbursement Point #1',
        siret: '111222333',
        id: 1,
        bic: 'BDFEFRPP',
        iban: 'FR9410010000000000000000022',
      },
    ])

    // When
    await renderReimbursementPoint(props)

    // Then
    expect(
      screen.getByRole('button', {
        name: 'Modifier mes coordonnées bancaires',
      })
    ).toBeInTheDocument()
  })

  it('should display banner when venue has dms application pending', async () => {
    // Given
    const venueWithPendingApplication = {
      id: 'AA',
      name: 'fake venue name',
      bix: null,
      iban: null,
      demarchesSimplifieesApplicationId: '2',
    }

    props.venue = venueWithPendingApplication
    pcapi.getBusinessUnits.mockResolvedValue([])

    // When
    await renderReimbursementPoint(props)

    // Then
    expect(
      screen.queryByText(
        'Les coordonnées bancaires de votre lieu sont en cours de validation par notre service financier.'
      )
    ).toBeInTheDocument()
  })
})