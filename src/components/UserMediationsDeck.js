import moment from 'moment'
import React, { Component } from 'react'
import { connect } from 'react-redux'
import { compose } from 'redux'

import Deck from './Deck'
import withSelectors from '../hocs/withSelectors'
import { requestData } from '../reducers/data'
import { closeLoading, showLoading } from '../reducers/loading'
import { getContentFromUserMediation } from '../utils/content'
import { sync } from '../utils/registerDexieServiceWorker'

class UserMediationsDeck extends Component {
  constructor() {
    super()
    this.state = { contents: null,
      hasSyncRequested: false,
      items: null
    }
  }
  handleCheckContent = props => {
    // unpack and check
    const { afterContents,
      aroundContent,
      beforeContents
    } = this
    const { requestData, handLength } = this.props
    const { hasSyncRequested } = this.state
    if (!aroundContent) {
      return
    }
    // from the present to the past
    // meet the first not well defined content
    for (let index of [...Array(handLength + 1).keys()]) {
      const content = beforeContents[handLength - 1 - index]
      // if it is not defined
      // it means we need to do ask the backend
      // to update the dexie blob at the good current around
      if (!content && !hasSyncRequested) {
        beforeContents[handLength - 1 - index] = { isLoading: true }
        this.setState({ contents: [
            ...beforeContents,
            aroundContent,
            ...afterContents
          ],
          hasSyncRequested: true
        })
        // sync('dexie-push-pull', { around: aroundContent.id })
        return
      } else if (!hasSyncRequested) {
        this.setState({ hasSyncRequested: false })
      }
    }
    // from the present to the future
    // meet the first not well defined content
    for (let index of [...Array(handLength + 1).keys()]) {
      const content = afterContents[index]
      // if it is not defined
      // it means we need to do ask the backend
      // to update the dexie blob at the good current around
      if (!content && !hasSyncRequested) {
        afterContents[index] = { isLoading: true }
        this.setState({ contents: [
            ...beforeContents,
            aroundContent,
            ...afterContents
          ],
          hasSyncRequested: true
        })
        // sync('dexie-push-pull', { around: aroundContent.id })
        return
      } else if (!hasSyncRequested) {
        this.setState({ hasSyncRequested: false })
      }
    }
  }
  handleSetContents = props => {
    // unpack and check
    const { isBlobModel,
      handLength,
      userMediations
    } = props
    if (!userMediations) {
      return
    }
    // determine automatically what should the actual aroundIndex
    // ie the index inside de userMediations dexie blob that
    // is the centered card
    let aroundContent, aroundIndex
    const dateReads = userMediations.map(userMediation =>
      userMediation.dateRead)
    const firstNotReadIndex = dateReads.indexOf(null)
    if (firstNotReadIndex === -1) {
      const lastReadIndex = dateReads.indexOf(Math.max(...dateReads))
      aroundIndex = lastReadIndex
    } else {
      aroundIndex = firstNotReadIndex
    }
    aroundContent = getContentFromUserMediation(userMediations[aroundIndex])
    // determine the before and after
    let afterContents, beforeContents
    // BLOB MODEL
    if (isBlobModel) {
      beforeContents = [...Array(userMediations.length - 2).keys()]
        .map(index => userMediations[aroundIndex - index - 1])
        .map(getContentFromUserMediation)
      beforeContents.reverse()
      afterContents = [...Array(userMediations.length - 2).keys()]
        .map(index => userMediations[aroundIndex + 1 + index])
        .map(getContentFromUserMediation)
    } else {
      // SLOT MODEL
      beforeContents = [...Array(handLength + 1).keys()]
        .map(index => userMediations[aroundIndex - handLength - 1 + index])
        .map(getContentFromUserMediation)
      afterContents = [...Array(handLength + 1).keys()]
        .map(index => userMediations[aroundIndex + 1 + index])
        .map(getContentFromUserMediation)
    }
    // concat
    const contents = [
      ...beforeContents,
      aroundContent,
      ...afterContents
    ]
    // update
    this.setState({ aroundIndex, contents })
  }
  onNextCard = (diffIndex, deckProps, deckState) => {
    // unpack
    const { handLength,
      isBlobModel,
      nextTimeout,
      userMediations
    } = this.props
    const { aroundIndex, contents } = this.state
    if (isBlobModel) {

    } else {
      // SLOT MODEL
      setTimeout(() => this.setState({
          aroundIndex: aroundIndex - diffIndex,
          contents: diffIndex === -1
            ? [
              ...contents.slice(1),
              getContentFromUserMediation(userMediations[aroundIndex + handLength + 2])
            ]
            : [
              getContentFromUserMediation(userMediations[aroundIndex - handLength - 2]),
              ...contents.slice(0, -1)
            ]
        }), nextTimeout)
    }
  }
  /*
  console.log('AVANT this.contents', this.contents.map(content => content && content.id))
  console.log('deckState.items', deckState.items)
  setTimeout(() => {
    const { handLength, userMediations } = this.props
    this.aroundIndex = this.aroundIndex - diffIndex
    this.aroundContent = getContentFromUserMediation(userMediations[this.aroundIndex])
    this.handleSetContents(this.props)
    // this.handleCheckContent(this.props)
    console.log('APRES this.contents', this.contents.map(content => content && content.id))
    // this.setState({ items: [...Array(2* handLength + 3).keys()] })
  }, 2000)
  */
  /*
  console.log('this.state.contents', this.state.contents.map(content =>
    content && content.id))
  */
  onReadCard = card => {
    // unpack
    const { requestData } = this.props
    // update dexie
    const nowDate = moment().toISOString()
    const body = [{
      dateRead: nowDate,
      dateUpdated: nowDate,
      id: card.content.id,
      isFavorite: card.content.isFavorite
    }]
    // requestData('PUT', 'userMediations', { body, sync: true })
  }
  componentWillMount () {
    this.handleSetContents(this.props)
  }
  componentWillReceiveProps (nextProps) {
    if (nextProps.userMediations !== this.props.userMediations) {
      this.handleSetContents(nextProps)
      // this.handleCheckContent(nextProps)
    }
  }
  render () {
    console.log('RENDER this.state.contents', this.state.contents && this.state.contents.map(content =>
      content && content.id))
    return <Deck {...this.props}
      {...this.state}
      onNextCard={this.onNextCard}
      onReadCard={this.onReadCard} />
  }
}

UserMediationsDeck.defaultProps = { handLength: 2,
  isBlobModel: false,
  nextTimeout: 500
}

export default compose(
  connect(
    (state, ownProps) => ({ userMediations: state.data.userMediations }),
    { requestData }
  )
)(UserMediationsDeck)
