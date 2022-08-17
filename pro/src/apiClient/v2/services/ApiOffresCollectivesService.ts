/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CollectiveOffersListResponseModel } from '../models/CollectiveOffersListResponseModel';
import type { GetPublicCollectiveOfferResponseModel } from '../models/GetPublicCollectiveOfferResponseModel';
import type { OfferStatus } from '../models/OfferStatus';
import type { PostCollectiveOfferBodyModel } from '../models/PostCollectiveOfferBodyModel';

import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';

export class ApiOffresCollectivesService {

  constructor(public readonly httpRequest: BaseHttpRequest) {}

  /**
   * Récuperation de l'offre collective avec l'identifiant offer_id. Cette api ignore les offre vitrines et les offres commencées sur l'interface web et non finalisées.
   * @param status
   * @param venueId
   * @param periodBeginningDate
   * @param periodEndingDate
   * @returns CollectiveOffersListResponseModel L'offre collective existe
   * @throws ApiError
   */
  public getCollectiveOffersPublic(
    status?: OfferStatus | null,
    venueId?: number | null,
    periodBeginningDate?: string | null,
    periodEndingDate?: string | null,
  ): CancelablePromise<CollectiveOffersListResponseModel> {
    return this.httpRequest.request({
      method: 'GET',
      url: '/v2/collective-offers/',
      query: {
        'status': status,
        'venueId': venueId,
        'periodBeginningDate': periodBeginningDate,
        'periodEndingDate': periodEndingDate,
      },
      errors: {
        401: `Authentification nécessaire`,
        403: `Vous n'avez pas les droits nécessaires pour voir cette offre collective`,
        404: `L'offre collective n'existe pas`,
        422: `Unprocessable Entity`,
      },
    });
  }

  /**
   * Création d'une offre collective.
   * @param requestBody
   * @returns GetPublicCollectiveOfferResponseModel L'offre collective existe
   * @throws ApiError
   */
  public postCollectiveOfferPublic(
    requestBody?: PostCollectiveOfferBodyModel,
  ): CancelablePromise<GetPublicCollectiveOfferResponseModel> {
    return this.httpRequest.request({
      method: 'POST',
      url: '/v2/collective-offers/',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        400: `Requête malformée`,
        401: `Authentification nécessaire`,
        403: `Non éligible pour les offres collectives`,
        422: `Unprocessable Entity`,
      },
    });
  }

}