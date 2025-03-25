package common

import (
	"errors"
	"net"
	"sync"
)

type Protocol struct {
	serverAddress string
	conn          net.Conn
	running       bool
	mutex         sync.Mutex
}

func NewProtocol(serverAddress string) *Protocol {
	return &Protocol{
		serverAddress: serverAddress,
	}
}

func (p *Protocol) Start() error {
	conn, err := net.Dial("tcp", p.serverAddress)
	if err != nil {
		return err
	}
	p.conn = conn
	p.running = true
	return nil
}

func (p *Protocol) Stop() error {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	p.running = false
	p.conn.Close()
	return nil
}

func (p *Protocol) SendMessage(message BetRequest) error {
	// Message type 0 for bet request
	msgType := []byte{0}

	// Convert name to bytes with 2-byte length prefix
	nameBytes := []byte(message.Name)
	nameLen := uint16(len(nameBytes))
	nameLenBytes := []byte{byte(nameLen >> 8), byte(nameLen)}

	// Convert surname to bytes with 2-byte length prefix
	surnameBytes := []byte(message.Surname)
	surnameLen := uint16(len(surnameBytes))
	surnameLenBytes := []byte{byte(surnameLen >> 8), byte(surnameLen)}

	// Convert document number to 4 bytes
	docNum := uint32(message.Document)
	docBytes := []byte{
		byte(docNum >> 24),
		byte(docNum >> 16),
		byte(docNum >> 8),
		byte(docNum),
	}

	// Convert birth date to 4 bytes (2 for year, 1 for month, 1 for day)
	year := uint16(message.Birthdate.Year())
	yearBytes := []byte{byte(year >> 8), byte(year)}
	monthByte := byte(message.Birthdate.Month())
	dayByte := byte(message.Birthdate.Day())

	// Convert bet number to 4 bytes
	betNum := uint32(message.Number)
	betNumBytes := []byte{
		byte(betNum >> 24),
		byte(betNum >> 16),
		byte(betNum >> 8),
		byte(betNum),
	}

	// Null terminator
	nullTerm := []byte{0}

	// Combine all parts
	msg := append(msgType, nameLenBytes...)
	msg = append(msg, nameBytes...)
	msg = append(msg, surnameLenBytes...)
	msg = append(msg, surnameBytes...)
	msg = append(msg, docBytes...)
	msg = append(msg, yearBytes...)
	msg = append(msg, monthByte)
	msg = append(msg, dayByte)
	msg = append(msg, betNumBytes...)
	msg = append(msg, nullTerm...)

	// Lock only when sending message
	p.mutex.Lock()
	defer p.mutex.Unlock()

	if !p.running {
		return errors.New("connection closed")
	}
	written := 0
	for written < len(msg) {
		n, err := p.conn.Write(msg[written:])
		if err != nil {
			return err
		}
		written += n
	}
	return nil
}
