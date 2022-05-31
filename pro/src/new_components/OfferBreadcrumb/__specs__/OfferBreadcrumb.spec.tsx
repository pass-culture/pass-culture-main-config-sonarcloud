import '@testing-library/jest-dom'
import { History, createBrowserHistory } from 'history'
import OfferBreadcrumb, { OfferBreadcrumbStep } from '../OfferBreadcrumb'
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import React from 'react'
import { Router } from 'react-router-dom'
import { Store } from 'redux'
import { configureTestStore } from 'store/testUtils'

describe('src | new_components | OfferBreadcrumb', () => {
  let store: Store
  let history: History

  beforeEach(() => {
    history = createBrowserHistory()
  })

  describe('Individual offer', () => {
    beforeEach(() => {
      store = configureTestStore({
        features: {
          initialized: true,
          list: [
            {
              nameKey: 'ENABLE_EDUCATIONAL_INSTITUTION_ASSOCIATION',
              isActive: false,
            },
          ],
        },
      })
    })

    it('should display breadcrumb for individual offer', async () => {
      render(
        <Router history={history}>
          <Provider store={store}>
            <OfferBreadcrumb
              activeStep={OfferBreadcrumbStep.DETAILS}
              isCreatingOffer={true}
              offerId="A1"
              isOfferEducational={false}
            />
          </Provider>
        </Router>
      )

      const listItems = await screen.findAllByRole('listitem')

      expect(listItems).toHaveLength(3)
      expect(listItems[0]).toHaveTextContent("Détails de l'offre")
      expect(listItems[1]).toHaveTextContent("Stock et prix")
      expect(listItems[2]).toHaveTextContent("Confirmation")
    })

    it('should generate link with offerId when user is editing an offer', async () => {
      render(
        <Router history={history}>
          <Provider store={store}>
            <OfferBreadcrumb
              activeStep={OfferBreadcrumbStep.DETAILS}
              isCreatingOffer={false}
              offerId="A1"
              isOfferEducational={false}
            />
          </Provider>
        </Router>
      )

      const linkItems = await screen.findAllByRole('link')

      expect(linkItems).toHaveLength(2)
      expect(linkItems[0].getAttribute('href')).toBe(
        '/offre/A1/individuel/edition'
      )
      expect(linkItems[1].getAttribute('href')).toBe(
        '/offre/A1/individuel/stocks'
      )
    })
  })

  describe('Collective offer - without domain association', () => {
    beforeEach(() => {
      store = configureTestStore({
        features: {
          initialized: true,
          list: [
            {
              nameKey: 'ENABLE_EDUCATIONAL_INSTITUTION_ASSOCIATION',
              isActive: false,
            },
          ],
        },
      })
    })

    it('should display breadcrumb for collective offer - without visibility step', async () => {
      render(
        <Router history={history}>
          <Provider store={store}>
            <OfferBreadcrumb
              activeStep={OfferBreadcrumbStep.DETAILS}
              isCreatingOffer={true}
              offerId="A1"
              isOfferEducational={true}
            />
          </Provider>
        </Router>
      )

      const listItems = await screen.findAllByRole('listitem')

      expect(listItems).toHaveLength(3)
      expect(listItems[0]).toHaveTextContent("Détails de l'offre")
      expect(listItems[1]).toHaveTextContent("Date et prix")
      expect(listItems[2]).toHaveTextContent("Confirmation")
    })
  })

  describe('Collective offer - with domain association', () => {
    beforeEach(() => {
      store = configureTestStore({
        features: {
          initialized: true,
          list: [
            {
              nameKey: 'ENABLE_EDUCATIONAL_INSTITUTION_ASSOCIATION',
              isActive: true,
            },
          ],
        },
      })
    })

    it('should display breadcrumb for collective offer - with visibility step', async () => {
      render(
        <Router history={history}>
          <Provider store={store}>
            <OfferBreadcrumb
              activeStep={OfferBreadcrumbStep.DETAILS}
              isCreatingOffer={true}
              offerId="A1"
              isOfferEducational={true}
            />
          </Provider>
        </Router>
      )

      const listItems = await screen.findAllByRole('listitem')

      expect(listItems).toHaveLength(4)
      expect(listItems[0]).toHaveTextContent("Détails de l'offre")
      expect(listItems[1]).toHaveTextContent("Date et prix")
      expect(listItems[2]).toHaveTextContent("Visibilité")
      expect(listItems[3]).toHaveTextContent("Confirmation")
    })

    it('collective offer - should generate link with offerId when user is editing an offer', async () => {
      render(
        <Router history={history}>
          <Provider store={store}>
            <OfferBreadcrumb
              activeStep={OfferBreadcrumbStep.DETAILS}
              isCreatingOffer={false}
              offerId="A1"
              isOfferEducational={true}
            />
          </Provider>
        </Router>
      )

      const linkItems = await screen.findAllByRole('link')

      expect(linkItems).toHaveLength(3)
      expect(linkItems[0].getAttribute('href')).toBe(
        '/offre/A1/collectif/edition'
      )
      expect(linkItems[1].getAttribute('href')).toBe(
        '/offre/A1/collectif/stocks/edition'
      )
      expect(linkItems[2].getAttribute('href')).toBe(
        '/offre/A1/collectif/visibilite/edition'
      )
    })
  })
})