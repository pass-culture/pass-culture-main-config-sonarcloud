import get from 'lodash.get'
import React, { Component } from 'react'
import { connect } from 'react-redux'
import { NavLink } from 'react-router-dom'
import { compose } from 'redux'

import MediationManager from '../MediationManager'
import OccasionForm from '../OccasionForm'
import withCurrentOccasion from '../hocs/withCurrentOccasion'
import FormField from '../layout/FormField'
import Label from '../layout/Label'
import PageWrapper from '../layout/PageWrapper'
import SubmitButton from '../layout/SubmitButton'
import Icon from '../layout/Icon'
import { resetForm } from '../../reducers/form'
import { showModal } from '../../reducers/modal'
import { showNotification } from '../../reducers/notification'
import eventSelector from '../../selectors/event'
import occurencesSelector from '../../selectors/occurences'
import offererSelector from '../../selectors/offerer'
import offerersSelector from '../../selectors/offerers'
import providersSelector from '../../selectors/providers'
import searchSelector from '../../selectors/search'
import thingSelector from '../../selectors/thing'
import typeSelector from '../../selectors/type'
import typesSelector from '../../selectors/types'
import venueSelector from '../../selectors/venue'
import venuesSelector from '../../selectors/venues'
import { NEW } from '../../utils/config'
import { getIsDisabled, optionify } from '../../utils/form'
import { eventNormalizer } from '../../utils/normalizers'
import { pluralize, updateQueryString } from '../../utils/string'



const requiredEventAndThingFields = [
  'author',
  'name',
  'type',
  'description',
  //'contactName',
  //'contactEmail',
  'performer',
  'stageDirector'
]

const requiredEventFields = [
  'durationMinutes',
]

class OccasionPage extends Component {
  constructor () {
    super()
    this.state = {
      isReadOnly: true,
      hasNoVenue: false
    }
  }

  static getDerivedStateFromProps (nextProps) {
    const {
      match: { params: { feature } },
      isNew,
      occasion,
      type,
    } = nextProps
    const {
      eventId,
      thingId
    } = (occasion || {})
    const isEdit = feature === 'modifie'
    const isEventType = eventId || get(type, 'model') === 'EventType'
    const isReadOnly = !isNew && !isEdit

    const apiPath = isEventType
      ? `events${eventId ? `/${eventId}` : ''}`
      : `things${thingId ? `/${thingId}` : ''}`

    let requiredFields = requiredEventAndThingFields

    if (isEventType) {
      requiredFields = requiredFields.concat(requiredEventFields)
    }

    return {
      apiPath,
      isEventType,
      isReadOnly,
      requiredFields
    }
  }

  handleDataRequest = (handleSuccess, handleFail) => {
    const {
      history,
      offerers,
      providers,
      requestData,
      showModal,
      typeOptions,
    } = this.props
    offerers.length === 0 && requestData(
      'GET',
      'offerers',
      {
        handleSuccess: (state, action) => {
          if (!get(state, 'data.venues.length')) {
            showModal(
              <div>
                Vous devez avoir déjà enregistré un lieu
                dans une de vos structures pour ajouter des offres
              </div>, {
                onCloseClick: () => history.push('/structures')
              })
          }
        },
        handleFail,
        normalizer: { managedVenues: 'venues' }
      }
    )
    providers.length === 0 && requestData('GET', 'providers')
    typeOptions.length === 0 && requestData('GET', 'types')

    handleSuccess()
  }

  handleFailData = (state, action) => {
    this.props.showNotification({
      type: 'danger',
      text: 'Un problème est survenu lors de l\'enregistrement',
    })
  }

  handleSuccessData = (state, action) => {
    const {
      data,
      method
    } = action
    const {
      occasion,
      history,
      showNotification,
      venue
    } = this.props
    const {
      isEventType
    } = this.state

    showNotification({
      text: 'Votre offre a bien été enregistrée',
      type: 'success'
    })

    // PATCH
    if (method === 'PATCH') {
      history.push(`/offres/${occasion.id}`)
      return
    }

    // POST
    if (isEventType && method === 'POST') {
      const { occasions } = (data || {})
      const occasion = occasions && occasions.find(o =>
        o.venueId === get(venue, 'id'))
      if (!occasion) {
        console.warn("Something wrong with returned data, we should retrieve the created occasion here")
        return
      }
      history.push(`/offres/${occasion.id}/dates?modifie`)
    }
  }

  componentDidUpdate () {
    const {
      history,
      offerer,
      search,
      venue
    } = this.props
    const { offererId, venueId } = this.props

    if (venue && venueId && venue.id !== venueId) {
      history.push({
        search: updateQueryString(search, { venueId })
      })
      return
    }
    if (offerer && offererId && offerer.id !== offererId) {
      history.push({
        search: updateQueryString(search, { offererId })
      })
    }
  }

  componentWillUnmount () {
    this.props.resetForm()
  }

  render () {
    const {
      event,
      isNew,
      location: { pathname, search },
      occasion,
      occurences,
      occasionIdOrNew,
      offerer,
      offerers,
      routePath,
      thing,
      type,
      typeOptions,
      venue,
      venues
    } = this.props
    const {
      extraData,
      name
    } = (event || thing || {})
    const {
      apiPath,
      isReadOnly,
      requiredFields
    } = this.state

    const typeOptionsWithPlaceholder = optionify(typeOptions, 'Sélectionnez un type d\'offre', o => o)
    const showAllForm = type || !isNew

    return (
      <PageWrapper
        backTo={{path: `/offres${search}`, label: 'Vos offres'}}
        name='offer'
        handleDataRequest={this.handleDataRequest}
      >
        <div className='section'>
          <h1 className='pc-title'>
            {
              isNew
                ? "Ajouter une"
                : "Détails de l'"
            } offre
          </h1>
          <p className='subtitle'>
            Renseignez les détails de cette offre et mettez-la en avant en ajoutant une ou plusieurs accorches.
          </p>
          <div className='field-group'>
            <FormField
              collectionName='occasions'
              defaultValue={name}
              entityId={occasionIdOrNew}
              isHorizontal
              isExpanded
              label={<Label title="Titre de l'offre :" />}
              name="name"
              readOnly={isReadOnly}
              required={!isReadOnly}
            />
            <FormField
              collectionName='occasions'
              defaultValue={get(type, 'value')}
              entityId={occasionIdOrNew}
              isHorizontal
              label={<Label title="Type :" />}
              name="type"
              options={(isReadOnly && !get(type, 'value') && []) || typeOptionsWithPlaceholder}
              readOnly={isReadOnly}
              required={!isReadOnly}
              type="select"
            />
          </div>
          {
            !isNew && (
              <div className='field'>
                {
                  event && (
                    <div className='field form-field is-horizontal'>
                      <div className='field-label'>
                        <label className="label" htmlFor="input_occasions_name">
                          <div className="subtitle">Dates :</div>
                        </label>
                      </div>
                      <div className='field-body'>
                        <div className='field'>
                          <div className='nb-dates'>
                            {pluralize(get(occurences, 'length'), 'date')}
                          </div>
                          <NavLink
                            className='button is-primary is-outlined is-small'
                            to={`${routePath}/dates`}
                          >
                            <span className='icon'><Icon svg='ico-calendar' /></span>
                            <span>Gérer les dates et les prix</span>
                          </NavLink>
                        </div>
                      </div>
                    </div>
                  )
                }
                <MediationManager
                  occasion={occasion}
                  routePath={routePath}
                />
              </div>
            )}
        </div>
        {
          showAllForm && <OccasionForm
            event={event}
            isNew={isNew}
            occasion={occasion}
            occasionIdOrNew={occasionIdOrNew}
            offerer={offerer}
            offerers={offerers}
            routePath={routePath}
            thing={thing}
            venue={venue}
            venues={venues}
            {...this.state}
          />
        }

        <hr />
        <div className="field is-grouped is-grouped-centered" style={{justifyContent: 'space-between'}}>
          <div className="control">
            {
              isReadOnly
                ? (
                  <NavLink to={`${pathname}/modifie${search}`}
                    className='button is-secondary is-medium'>
                    Modifier l'offre
                  </NavLink>
                )
                : (
                  <NavLink
                    className="button is-secondary is-medium"
                    to={`/offres${search}`}>
                    Annuler
                  </NavLink>
                )
            }
          </div>
          <div className="control">
            {
              isReadOnly
                ? (
                  <NavLink to={`/offres${search}`} className='button is-primary is-medium'>
                    Terminer
                  </NavLink>
                )
                : (
                  <SubmitButton
                    className="button is-primary is-medium"
                    getBody={form => {
                      const occasionForm = Object.assign({},
                        get(form, `occasionsById.${occasionIdOrNew}`))
                      // remove the EventType. ThingType.
                      if (occasionForm.type) {
                        occasionForm.type = occasionForm.type.split('.')[1]
                      }

                      const { author, performer, stageDirector } = occasionForm
                      occasionForm.extraData = Object.assign({
                        author, performer, stageDirector
                      }, extraData)

                      return occasionForm
                    }}
                    getIsDisabled={form => getIsDisabled(
                        get(form, `occasionsById.${occasionIdOrNew}`),
                        requiredFields,
                        isNew
                      )
                    }
                    handleSuccess={this.handleSuccessData}
                    handleFail={this.handleFailData}
                    normalizer={eventNormalizer}
                    method={isNew ? 'POST' : 'PATCH'}
                    path={apiPath}
                    storeKey="events"
                    text="Enregistrer"
                  />
                )
              }
          </div>
        </div>
      </PageWrapper>
    )
  }
}

export default compose(
  withCurrentOccasion,
  connect(
    (state, ownProps) => {
      const eventId = get(ownProps, 'occasion.eventId')
      const occasionId = get(ownProps, 'occasion.id') || NEW
      const thingId = get(ownProps, 'occasion.thingId')
      const formLabel = get(state, `form.occasionsById.${occasionId}.type`)
      const search = searchSelector(state, ownProps.location.search)

      const newState = {
        event: eventSelector(state, eventId),
        offerers: offerersSelector(state),
        providers: providersSelector(state),
        search,
        thing: thingSelector(state, thingId),
        type: typeSelector(state, eventId, thingId, formLabel),
        typeOptions: typesSelector(state),

      }

      // CASE WHERE ALL IS DECIDED FROM THE SELECTS
      let offererId = get(state, `form.occasionsById.${occasionId}.offererId`)
      if (offererId) {
        newState.offerer = offererSelector(state, offererId)
        newState.venues = venuesSelector(state, offererId)
        if (get(newState.venues, 'length') === 1) {
          newState.venue = get(newState.venues, '0')
        }
        return newState
      }

      let venueId = get(state, `form.occasionsById.${occasionId}.venueId`)
      if (venueId) {
        newState.venue = venueSelector(state, venueId)
        newState.offerer = offererSelector(state, get(newState.venue, 'managingOffererId'))
        newState.venues = venuesSelector(state, offererId)
        return newState
      }

      // CASE WHERE ALL IS DECIDED FROM THE SEARCH
      venueId = search.venueId
      if (venueId) {
        newState.venue = venueSelector(state, venueId)
        newState.venues = [newState.venue]
        newState.offerer = offererSelector(state, get(newState.venue, 'managingOffererId'))
        newState.offerers = [newState.offerer]
        return newState
      }
      offererId = search.offererId
      if (offererId) {
        newState.offerer = offererSelector(state, offererId)
        newState.offerers = [newState.offerer]
        newState.venues = venuesSelector(state, offererId)
        if (get(newState.venues, 'length') === 1) {
          newState.venue = get(newState.venues, '0')
        }
        return newState
      }

      // CASE WHERE ALL IS DECIDED FROM THE OCCASION
      venueId = get(ownProps, 'occasion.venueId')
      if (venueId) {
        newState.venue = venueSelector(state, venueId)
        newState.venues = [newState.venue]
        newState.offerer = offererSelector(state, get(newState.venue, 'managingOffererId'))
        newState.occurences = occurencesSelector(state, venueId, eventId)
        return newState
      }
      offererId = get(ownProps, 'occasion.offererId')
      if (offererId) {
        newState.offerer = offererSelector(state, offererId)
        newState.venues = venuesSelector(state, offererId)
        if (get(newState.venues, 'length') === 1) {
          newState.venue = get(newState.venues, '0')
        }
        return newState
      }

      // CASE WHERE WE DON T KNOW YET
      // BUT MAYBE WE HAVE ONLY ONE OFFERER
      if (get(newState.offerers, 'length') === 1) {
        newState.offerer = get(newState.offerers, '0')
      }
      return newState
    },
    {
      resetForm,
      showModal,
      showNotification
    }
  )
)(OccasionPage)
