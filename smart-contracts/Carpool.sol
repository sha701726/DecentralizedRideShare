// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Carpool
 * @dev A smart contract for decentralized carpooling services
 */
contract Carpool {
    // Structs
    struct Ride {
        address payable driver;    // Driver's wallet address
        string startLocation;      // Start location of the ride
        string endLocation;        // End location of the ride
        uint256 price;             // Price per seat in wei
        uint8 availableSeats;      // Number of available seats
        bool isAvailable;          // Whether the ride is still available for booking
        uint256 createdAt;         // Timestamp when the ride was created
    }
    
    struct Booking {
        address passenger;         // Passenger's wallet address
        uint256 rideId;            // ID of the ride being booked
        uint8 seatsBooked;         // Number of seats booked
        uint256 totalAmount;       // Total amount paid (price * seatsBooked)
        bool isCompleted;          // Whether the ride has been completed
        uint256 createdAt;         // Timestamp when the booking was created
    }
    
    // State variables
    mapping(uint256 => Ride) public rides;
    mapping(uint256 => Booking[]) public bookings;
    uint256 public rideCount;
    uint256 public bookingCount;
    
    // Events
    event RideCreated(uint256 indexed rideId, address indexed driver, uint256 price, uint8 availableSeats);
    event RideBooked(uint256 indexed rideId, address indexed passenger, uint8 seatsBooked, uint256 amount);
    event RideCompleted(uint256 indexed rideId, address indexed driver);
    event RideCancelled(uint256 indexed rideId, address indexed driver);
    event BookingCancelled(uint256 indexed bookingId, address indexed passenger);
    
    // Modifiers
    modifier onlyDriver(uint256 _rideId) {
        require(msg.sender == rides[_rideId].driver, "Only the driver can perform this action");
        _;
    }
    
    /**
     * @dev Create a new ride
     * @param _startLocation Start location of the ride
     * @param _endLocation End location of the ride
     * @param _price Price per seat in wei
     * @param _availableSeats Number of available seats
     */
    function createRide(
        string memory _startLocation,
        string memory _endLocation,
        uint256 _price,
        uint8 _availableSeats
    ) public returns (uint256) {
        require(_availableSeats > 0, "Available seats must be greater than 0");
        require(_price > 0, "Price must be greater than 0");
        
        rideCount++;
        
        rides[rideCount] = Ride({
            driver: payable(msg.sender),
            startLocation: _startLocation,
            endLocation: _endLocation,
            price: _price,
            availableSeats: _availableSeats,
            isAvailable: true,
            createdAt: block.timestamp
        });
        
        emit RideCreated(rideCount, msg.sender, _price, _availableSeats);
        
        return rideCount;
    }
    
    /**
     * @dev Book a ride
     * @param _rideId ID of the ride to book
     * @param _seatsToBook Number of seats to book
     */
    function bookRide(uint256 _rideId, uint8 _seatsToBook) public payable {
        Ride storage ride = rides[_rideId];
        
        require(ride.driver != address(0), "Ride does not exist");
        require(ride.isAvailable, "Ride is not available");
        require(_seatsToBook > 0, "Seats to book must be greater than 0");
        require(_seatsToBook <= ride.availableSeats, "Not enough seats available");
        require(msg.value >= ride.price * _seatsToBook, "Insufficient payment");
        
        // Create a new booking
        bookingCount++;
        Booking memory newBooking = Booking({
            passenger: msg.sender,
            rideId: _rideId,
            seatsBooked: _seatsToBook,
            totalAmount: msg.value,
            isCompleted: false,
            createdAt: block.timestamp
        });
        
        // Add booking to the ride's bookings
        bookings[_rideId].push(newBooking);
        
        // Update available seats
        ride.availableSeats -= _seatsToBook;
        
        // Check if all seats are booked
        if (ride.availableSeats == 0) {
            ride.isAvailable = false;
        }
        
        // Transfer payment to driver (in a production environment, 
        // we would likely hold this in escrow until the ride is completed)
        ride.driver.transfer(msg.value);
        
        emit RideBooked(_rideId, msg.sender, _seatsToBook, msg.value);
    }
    
    /**
     * @dev Get ride details
     * @param _rideId ID of the ride
     */
    function getRide(uint256 _rideId) public view returns (
        address driver,
        string memory startLocation,
        string memory endLocation,
        uint256 price,
        uint8 availableSeats,
        bool isAvailable
    ) {
        Ride memory ride = rides[_rideId];
        return (
            ride.driver,
            ride.startLocation,
            ride.endLocation,
            ride.price,
            ride.availableSeats,
            ride.isAvailable
        );
    }
    
    /**
     * @dev Mark a ride as completed
     * @param _rideId ID of the ride to complete
     */
    function completeRide(uint256 _rideId) public onlyDriver(_rideId) {
        Ride storage ride = rides[_rideId];
        require(ride.isAvailable == false || ride.availableSeats == 0, "Ride must be fully booked or marked unavailable");
        
        // In a production environment, this would release the escrowed payments to the driver
        
        emit RideCompleted(_rideId, msg.sender);
    }
    
    /**
     * @dev Cancel a ride by the driver
     * @param _rideId ID of the ride to cancel
     */
    function cancelRide(uint256 _rideId) public onlyDriver(_rideId) {
        Ride storage ride = rides[_rideId];
        require(ride.isAvailable, "Ride is already unavailable or completed");
        
        // In a production environment, this would refund any escrowed payments back to passengers
        
        ride.isAvailable = false;
        emit RideCancelled(_rideId, msg.sender);
    }
    
    /**
     * @dev Get bookings for a ride
     * @param _rideId ID of the ride
     */
    function getRideBookings(uint256 _rideId) public view returns (Booking[] memory) {
        return bookings[_rideId];
    }
    
    /**
     * @dev Get the total number of rides
     */
    function getRideCount() public view returns (uint256) {
        return rideCount;
    }
    
    /**
     * @dev Get all active rides (for frontend pagination)
     * @param _offset Starting index
     * @param _limit Maximum number of rides to return
     */
    function getActiveRides(uint256 _offset, uint256 _limit) public view returns (
        uint256[] memory rideIds,
        address[] memory drivers,
        string[] memory startLocations,
        string[] memory endLocations,
        uint256[] memory prices,
        uint8[] memory availableSeats
    ) {
        // Count active rides first
        uint256 activeCount = 0;
        uint256[] memory activeIndices = new uint256[](rideCount);
        
        for (uint256 i = 1; i <= rideCount; i++) {
            if (rides[i].isAvailable && rides[i].availableSeats > 0) {
                activeIndices[activeCount] = i;
                activeCount++;
            }
        }
        
        // Determine the actual result size (respecting offset and limit)
        uint256 resultSize = 0;
        if (_offset < activeCount) {
            resultSize = (activeCount - _offset) < _limit ? (activeCount - _offset) : _limit;
        }
        
        // Initialize return arrays
        rideIds = new uint256[](resultSize);
        drivers = new address[](resultSize);
        startLocations = new string[](resultSize);
        endLocations = new string[](resultSize);
        prices = new uint256[](resultSize);
        availableSeats = new uint8[](resultSize);
        
        // Populate return arrays
        for (uint256 i = 0; i < resultSize; i++) {
            uint256 rideId = activeIndices[_offset + i];
            Ride storage ride = rides[rideId];
            
            rideIds[i] = rideId;
            drivers[i] = ride.driver;
            startLocations[i] = ride.startLocation;
            endLocations[i] = ride.endLocation;
            prices[i] = ride.price;
            availableSeats[i] = ride.availableSeats;
        }
        
        return (rideIds, drivers, startLocations, endLocations, prices, availableSeats);
    }
}
