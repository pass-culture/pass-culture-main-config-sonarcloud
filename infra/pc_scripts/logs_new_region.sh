#!/env/bash

function logs {
    if [[ "$ENV" == "development" ]]; then
        docker-compose -f docker-compose-app.yml logs
        exit
    else
        if [[ $# -gt 0 ]]; then
            scalingo -a "$SCALINGO_APP" logs "$@"
        else
            scalingo -a "$SCALINGO_APP" logs -n 100
        fi
        exit
    fi
}