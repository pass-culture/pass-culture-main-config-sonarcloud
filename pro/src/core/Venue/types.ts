import { GetVenueResponseModel } from 'apiClient/v1'
import { IVenueBannerMetaProps } from 'components/pages/Offerers/Offerer/VenueV1/VenueEdition/ImageVenueUploaderSection/ImageVenueUploaderSection'
import { IAccessibiltyFormValues } from 'core/shared'

// TODO use api/gen types
export interface IAPIVenue {
  address: string
  audioDisabilityCompliant: boolean
  bannerMeta: string | null
  bannerUrl: string | null
  bic: string
  bookingEmail: string
  businessUnitId: string
  city: string
  comment: null
  dateCreated: string
  dateModifiedAtLastProvider: string
  departementCode: string
  description: string
  fieldsUpdated: []
  iban: string
  id: string
  isPermanent: true
  isVirtual: boolean
  lastProviderId: null
  latitude: number
  longitude: number
  managingOffererId: string
  mentalDisabilityCompliant: boolean
  motorDisabilityCompliant: boolean
  nonHumanizedId: number
  nOffers: number
  name: string
  postalCode: string
  publicName: string
  pricingPoint: {
    id: number
    siret: string
    venueName: string
  }
  pricingPointId: number | null
  siret: string
  thumbCount: number
  venueLabelId: string | null
  venueTypeCode: string
  visualDisabilityCompliant: boolean
  withdrawalDetails: string | null
}

export type TOfferIndividualVenue = {
  id: string
  managingOffererId: string
  name: string
  isVirtual: boolean
  withdrawalDetails: string | null
  accessibility: IAccessibiltyFormValues
}

export type VenueCollectiveInformation = Pick<
  GetVenueResponseModel,
  | 'collectiveDescription'
  | 'collectiveDomains'
  | 'collectiveEmail'
  | 'collectiveInterventionArea'
  | 'collectiveLegalStatus'
  | 'collectiveNetwork'
  | 'collectivePhone'
  | 'collectiveStudents'
  | 'collectiveWebsite'
>

export interface IVenue {
  accessibility: IAccessibiltyFormValues
  address: string
  bannerMeta: IVenueBannerMetaProps | null | undefined
  bannerUrl: string
  city: string
  comment: string
  contact: {
    email: string
    phoneNumber: string
    webSite: string
  }
  description: string
  departmentCode: string
  id: string
  isPermanent: boolean
  isVenueVirtual: boolean
  latitude: number
  longitude: number
  mail: string
  name: string
  postalCode: string
  publicName: string
  siret: string
  venueType: string
  venueLabel: string
}

export type IProviders = {
  enabledForPro: boolean
  id: string
  isActive: boolean
  name: string
}

export type IVenueProviderApi = {
  id: string
  idAtProviders: string | null
  dateModifiedAtLastProvider: string | null
  isActive: boolean
  isFromAllocineProvider: boolean
  lastProviderId: string | null
  lastSyncDate: string | null
  nOffers: number
  providerId: string
  venueId: string
  venueIdAtOfferProvider: string
  provider: any
  quantity?: number
  isDuo: boolean | null
  price: number
}
