import React, { Fragment, useEffect, useMemo, useState } from 'react'
import type { Column } from 'react-table'

import {
  BookingRecapResponseModel,
  CollectiveBookingResponseModel,
} from 'apiClient/v1'

import {
  BeneficiaryCell,
  BookingTokenCell,
  BookingStatusCell,
  BookingOfferCell,
  BookingIsDuoCell,
  BookingDateCell,
  FilterByOmniSearch,
  Header,
  NoFilteredBookings,
  FilterByBookingStatus,
  ALL_BOOKING_STATUS,
  DEFAULT_OMNISEARCH_CRITERIA,
  EMPTY_FILTER_VALUE,
  TableWrapper,
} from './components'
import { NB_BOOKINGS_PER_PAGE } from './constants'
import { BookingsFilters } from './types'
import {
  filterBookingsRecap,
  sortByBeneficiaryName,
  sortByBookingDate,
  sortByOfferName,
} from './utils'

const FIRST_PAGE_INDEX = 0

interface IBookingsRecapTableProps<
  T extends BookingRecapResponseModel | CollectiveBookingResponseModel
> {
  bookingsRecap: T[]
  isLoading: boolean
  locationState?: {
    statuses: string[]
  }
}

// TODO: return columns depending on audience
const getColumnsByAudience = <
  T extends BookingRecapResponseModel | CollectiveBookingResponseModel
>(
  bookingStatus: string[],
  bookingsRecap: T[],
  updateGlobalFilters: (updatedFilters: Partial<BookingsFilters>) => void
): (Column<T> & {
  className?: string
})[] => {
  const columns: (Column<BookingRecapResponseModel> & {
    className?: string
  })[] = [
    {
      id: 'stock',
      accessor: 'stock',
      Header: "Nom de l'offre",
      Cell: ({ value }) => <BookingOfferCell offer={value} />,
      defaultCanSort: true,
      sortType: sortByOfferName,
      className: 'column-offer-name',
    },
    {
      id: 'booking_is_duo',
      accessor: 'booking_is_duo',
      Header: '',
      Cell: ({ value }) => <BookingIsDuoCell isDuo={value} />,
      disableSortBy: true,
      className: 'column-booking-duo',
    },
    {
      Header: 'Bénéficiaire',
      id: 'beneficiary',
      accessor: 'beneficiary',
      Cell: ({ value }) => <BeneficiaryCell beneficiaryInfos={value} />,
      defaultCanSort: true,
      sortType: sortByBeneficiaryName,
      className: 'column-beneficiary',
    },
    {
      Header: 'Réservation',
      id: 'booking_date',
      accessor: 'booking_date',
      Cell: ({ value }) => <BookingDateCell bookingDateTimeIsoString={value} />,
      defaultCanSort: true,
      sortType: sortByBookingDate,
      className: 'column-booking-date',
    },
    {
      Header: 'Contremarque',
      id: 'booking_token',
      accessor: 'booking_token',
      Cell: ({ value }) => <BookingTokenCell bookingToken={value} />,
      disableSortBy: true,
      className: 'column-booking-token',
    },
    {
      id: 'booking_status',
      accessor: 'booking_status',
      Cell: ({ row }) => {
        return <BookingStatusCell bookingRecapInfo={row} />
      },
      disableSortBy: true,
      Header: () => (
        <FilterByBookingStatus
          bookingStatuses={bookingStatus}
          bookingsRecap={bookingsRecap}
          updateGlobalFilters={updateGlobalFilters}
        />
      ),
      className: 'column-booking-status',
    },
  ]
  return columns as (Column<T> & {
    className?: string
  })[]
}

const BookingsRecapTable = <
  T extends BookingRecapResponseModel | CollectiveBookingResponseModel
>({
  bookingsRecap,
  isLoading,
  locationState,
}: IBookingsRecapTableProps<T>) => {
  const [filteredBookings, setFilteredBookings] = useState(bookingsRecap)
  const [currentPage, setCurrentPage] = useState(FIRST_PAGE_INDEX)

  const [filters, setFilters] = useState<BookingsFilters>({
    bookingBeneficiary: EMPTY_FILTER_VALUE,
    bookingToken: EMPTY_FILTER_VALUE,
    offerISBN: EMPTY_FILTER_VALUE,
    offerName: EMPTY_FILTER_VALUE,
    bookingStatus: locationState?.statuses.length
      ? locationState.statuses
      : [...ALL_BOOKING_STATUS],
    selectedOmniSearchCriteria: DEFAULT_OMNISEARCH_CRITERIA,
    keywords: '',
  })

  useEffect(() => {
    applyFilters()
  }, [bookingsRecap])

  const updateCurrentPage = (currentPage: number) => {
    setCurrentPage(currentPage)
  }

  const updateGlobalFilters = (updatedFilters: Partial<BookingsFilters>) => {
    setFilters(filters => {
      const newFilters = { ...filters, ...updatedFilters }
      applyFilters(newFilters)
      return newFilters
    })
  }

  const applyFilters = (filtersBookingResults?: BookingsFilters) => {
    const filtersToApply = filtersBookingResults || filters
    const bookingsRecapFiltered = filterBookingsRecap(
      bookingsRecap,
      filtersToApply
    )
    setFilteredBookings(bookingsRecapFiltered)
    setCurrentPage(FIRST_PAGE_INDEX)
  }

  const resetAllFilters = () => {
    const filtersBookingResults = {
      bookingBeneficiary: EMPTY_FILTER_VALUE,
      bookingToken: EMPTY_FILTER_VALUE,
      offerISBN: EMPTY_FILTER_VALUE,
      offerName: EMPTY_FILTER_VALUE,
      bookingStatus: [...ALL_BOOKING_STATUS],
      keywords: '',
      selectedOmniSearchCriteria: DEFAULT_OMNISEARCH_CRITERIA,
    }
    setFilters(filtersBookingResults)
    applyFilters(filtersBookingResults)
  }

  const updateFilters = (
    updatedFilter: Partial<BookingsFilters>,
    updatedSelectedContent: {
      keywords: string
      selectedOmniSearchCriteria: string
    }
  ) => {
    const { keywords, selectedOmniSearchCriteria } = updatedSelectedContent
    setFilters(filters => ({
      ...filters,
      ...updatedFilter,
      keywords,
      selectedOmniSearchCriteria,
    }))
    applyFilters({
      ...filters,
      ...updatedFilter,
    })
  }

  const nbBookings = filteredBookings.length

  const columns: (Column<T> & {
    className?: string
  })[] = useMemo(
    () =>
      getColumnsByAudience(
        filters.bookingStatus,
        bookingsRecap,
        updateGlobalFilters
      ),
    []
  )

  return (
    <div>
      <div className="filters-wrapper">
        <FilterByOmniSearch
          isDisabled={isLoading}
          keywords={filters.keywords}
          selectedOmniSearchCriteria={filters.selectedOmniSearchCriteria}
          updateFilters={updateFilters}
        />
      </div>
      {nbBookings > 0 ? (
        <Fragment>
          <Header
            bookingsRecapFilteredLength={filteredBookings.length}
            isLoading={isLoading}
          />
          <TableWrapper
            columns={columns}
            currentPage={currentPage}
            data={filteredBookings}
            nbBookings={nbBookings}
            nbBookingsPerPage={NB_BOOKINGS_PER_PAGE}
            updateCurrentPage={updateCurrentPage}
          />
        </Fragment>
      ) : (
        <NoFilteredBookings resetFilters={resetAllFilters} />
      )}
    </div>
  )
}

export default BookingsRecapTable
