package common

import "time"

type BetRequest struct {
	Name     string
	Surname  string
	Birthdate time.Time
	Document int
	Number   int
}
