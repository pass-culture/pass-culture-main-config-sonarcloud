import { SET_FEATURES, SET_FEATURES_IS_INITIALIZED } from './actions'

export const initialState = {
  initialized: false,
  list: [],
}

export const featuresReducer = (state = initialState, action) => {
  switch (action.type) {
    case SET_FEATURES_IS_INITIALIZED:
      return { ...state, initialized: true }
    case SET_FEATURES:
      return { ...state, list: action.features }
    default:
      return state
  }
}
