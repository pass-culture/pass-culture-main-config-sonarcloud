import React, { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import ActionsBarPortal from 'components/layout/ActionsBarPortal/ActionsBarPortal'
import PageTitle from 'components/layout/PageTitle/PageTitle'
import Titles from 'components/layout/Titles/Titles'
import ActionsBarContainer from 'components/pages/Offers/Offers/ActionsBar/ActionsBarContainer'
import NoOffers from 'components/pages/Offers/Offers/NoOffers/NoOffers'
import OffersContainer from 'components/pages/Offers/Offers/OffersContainer'
import {
  DEFAULT_SEARCH_FILTERS,
  MAX_TOTAL_PAGES,
  NUMBER_OF_OFFERS_PER_PAGE,
} from 'core/Offers'
import { Audience, Offer, Offerer, SearchFilters } from 'core/Offers/types'
import { ReactComponent as AddOfferSvg } from 'icons/ico-plus.svg'

import OfferListFilterTabs from './OfferListFilterTabs'

export interface IOffersProps {
  currentPageNumber: number
  currentUser: { isAdmin: boolean }
  isLoading: boolean
  loadAndUpdateOffers: (filters: SearchFilters) => Promise<void>
  offerer: Offerer | null
  offers: Offer[]
  setIsLoading: (isLoading: boolean) => void
  setOfferer: (offerer: Offerer | null) => void
  urlSearchFilters: SearchFilters
  separateIndividualAndCollectiveOffers: boolean
  initialSearchFilters: SearchFilters
  urlAudience: Audience
  redirectWithUrlFilters: (
    filters: SearchFilters & {
      page?: number
      audience?: Audience
    }
  ) => void
}

const Offers = ({
  currentPageNumber,
  currentUser,
  isLoading,
  loadAndUpdateOffers,
  offerer,
  offers,
  setIsLoading,
  setOfferer,
  urlSearchFilters,
  separateIndividualAndCollectiveOffers,
  initialSearchFilters,
  urlAudience,
  redirectWithUrlFilters,
}: IOffersProps): JSX.Element => {
  const [searchFilters, setSearchFilters] =
    useState<SearchFilters>(initialSearchFilters)
  const [isRefreshingOffers, setIsRefreshingOffers] = useState(true)

  const [areAllOffersSelected, setAreAllOffersSelected] = useState(false)
  const [selectedOfferIds, setSelectedOfferIds] = useState<string[]>([])
  const [selectedAudience, setSelectedAudience] =
    useState<Audience>(urlAudience)

  const { isAdmin } = currentUser || {}
  const currentPageOffersSubset = offers.slice(
    (currentPageNumber - 1) * NUMBER_OF_OFFERS_PER_PAGE,
    currentPageNumber * NUMBER_OF_OFFERS_PER_PAGE
  )
  const hasOffers = currentPageOffersSubset.length > 0
  const hasSearchFilters = useCallback(
    (
      searchFilters: SearchFilters,
      filterNames: (keyof SearchFilters)[] = Object.keys(
        searchFilters
      ) as (keyof SearchFilters)[]
    ) => {
      return filterNames
        .map(
          filterName =>
            searchFilters[filterName] !==
            { ...DEFAULT_SEARCH_FILTERS }[filterName]
        )
        .includes(true)
    },
    []
  )

  const userHasNoOffers =
    !isLoading && !hasOffers && !hasSearchFilters(urlSearchFilters)

  const actionLink =
    userHasNoOffers || isAdmin ? null : (
      <Link className="primary-button with-icon" to="/offre/creation">
        <AddOfferSvg />
        Créer une offre
      </Link>
    )

  const nbSelectedOffers = areAllOffersSelected
    ? offers.length
    : selectedOfferIds.length

  const clearSelectedOfferIds = useCallback(() => {
    setSelectedOfferIds([])
  }, [])

  const refreshOffers = useCallback(
    () => loadAndUpdateOffers(initialSearchFilters),
    [loadAndUpdateOffers, initialSearchFilters]
  )

  const toggleSelectAllCheckboxes = useCallback(() => {
    setAreAllOffersSelected(currentValue => !currentValue)
  }, [])

  const resetFilters = useCallback(() => {
    setIsLoading(true)
    setOfferer(null)
    setSearchFilters({ ...DEFAULT_SEARCH_FILTERS })
  }, [setSearchFilters, setIsLoading, setOfferer])

  const numberOfPages = Math.ceil(offers.length / NUMBER_OF_OFFERS_PER_PAGE)
  const pageCount = Math.min(numberOfPages, MAX_TOTAL_PAGES)

  useEffect(() => {
    if (isRefreshingOffers) {
      setSearchFilters(initialSearchFilters)
      loadAndUpdateOffers(initialSearchFilters)
    }
  }, [
    isRefreshingOffers,
    loadAndUpdateOffers,
    setSearchFilters,
    initialSearchFilters,
  ])

  const applyUrlFiltersAndRedirect = useCallback(
    (
      filters: SearchFilters & {
        page?: number
        audience?: Audience
      },
      isRefreshing = true
    ) => {
      setIsRefreshingOffers(isRefreshing)
      redirectWithUrlFilters(filters)
    },
    [setIsRefreshingOffers, redirectWithUrlFilters]
  )

  const onSelectAudience = (selectedAudience: Audience) => {
    applyUrlFiltersAndRedirect({
      ...DEFAULT_SEARCH_FILTERS,
      audience: selectedAudience,
    })
  }

  useEffect(() => {
    setSelectedAudience(urlAudience)
  }, [urlAudience])

  return (
    <div className="offers-page">
      <PageTitle title="Vos offres" />
      <Titles action={actionLink} title="Offres" />
      {separateIndividualAndCollectiveOffers && (
        <OfferListFilterTabs
          onSelectAudience={onSelectAudience}
          selectedAudience={selectedAudience}
        />
      )}
      <ActionsBarPortal isVisible={nbSelectedOffers > 0}>
        <ActionsBarContainer
          areAllOffersSelected={areAllOffersSelected}
          clearSelectedOfferIds={clearSelectedOfferIds}
          nbSelectedOffers={nbSelectedOffers}
          refreshOffers={refreshOffers}
          selectedOfferIds={selectedOfferIds}
          toggleSelectAllCheckboxes={toggleSelectAllCheckboxes}
        />
      </ActionsBarPortal>
      {userHasNoOffers ? (
        <NoOffers />
      ) : (
        <>
          <h3 className="op-title">Rechercher une offre</h3>
          {hasSearchFilters(searchFilters) ? (
            <Link
              className="reset-filters-link"
              onClick={resetFilters}
              to="/offres"
            >
              Réinitialiser les filtres
            </Link>
          ) : (
            <span className="reset-filters-link disabled">
              Réinitialiser les filtres
            </span>
          )}
        </>
      )}
      <OffersContainer
        applyUrlFiltersAndRedirect={applyUrlFiltersAndRedirect}
        areAllOffersSelected={areAllOffersSelected}
        currentPageNumber={currentPageNumber}
        currentPageOffersSubset={currentPageOffersSubset}
        currentUser={currentUser}
        hasOffers={hasOffers}
        hasSearchFilters={hasSearchFilters}
        isLoading={isLoading}
        offerer={offerer}
        offersCount={offers.length}
        pageCount={pageCount}
        refreshOffers={refreshOffers}
        resetFilters={resetFilters}
        searchFilters={searchFilters}
        selectedOfferIds={selectedOfferIds}
        setIsLoading={setIsLoading}
        setOfferer={setOfferer}
        setSearchFilters={setSearchFilters}
        setSelectedOfferIds={setSelectedOfferIds}
        toggleSelectAllCheckboxes={toggleSelectAllCheckboxes}
        urlSearchFilters={urlSearchFilters}
      />
    </div>
  )
}

export default Offers