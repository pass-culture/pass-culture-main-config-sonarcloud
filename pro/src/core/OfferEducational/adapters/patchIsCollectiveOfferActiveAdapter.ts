import * as pcapi from 'repository/pcapi/pcapi'

type IPayloadSuccess = null
type IPayloadFailure = null
type PatchIsOfferActiveAdapter = Adapter<
  { offerId: string; isActive: boolean },
  IPayloadSuccess,
  IPayloadFailure
>

export const patchIsCollectiveOfferActiveAdapter: PatchIsOfferActiveAdapter =
  async ({ offerId, isActive }) => {
    try {
      // the api returns no understandable error when the id is not valid, so we deal before calling the api
      if (!offerId || offerId === '')
        throw new Error('L’identifiant de l’offre n’est pas valide.')

      await pcapi.patchIsCollectiveOfferActive([offerId], isActive)

      return {
        isOk: true,
        message: isActive
          ? 'Votre offre est maintenant active et visible dans ADAGE.'
          : 'Votre offre est maintenant inactive et sera invisible pour les utilisateurs d’ADAGE.',
        payload: null,
      }
    } catch (error) {
      return {
        isOk: false,
        message: `Une erreur est survenue lors de ${
          isActive ? 'l’activation' : 'la désactivation'
        } de votre offre. ${
          // @ts-ignore
          error?.message ?? ''
        }`,
        payload: null,
      }
    }
  }
