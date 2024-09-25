package com.exam.examserver.models;

import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.ManyToOne;

@Entity
public class UserRole {
	@Id
	@GeneratedValue(strategy = GenerationType.AUTO)
	private Long userRoleid;
	@ManyToOne(fetch=FetchType.EAGER)
	private Users user;
	@ManyToOne
	private Role role;
	public Long getUserRoleid() {
		return userRoleid;
	}
	public void setUserRoleid(Long userRoleid) {
		this.userRoleid = userRoleid;
	}
	public Users getUser() {
		return user;
	}
	public void setUser(Users user) {
		this.user = user;
	}
	public UserRole() {
		super();
		// TODO Auto-generated constructor stub
	}
	public Role getRole() {
		return role;
	}
	public void setRole(Role role) {
		this.role = role;
	}
	

}
