// Demo only: credentials are stored in browser localStorage.
// Do not use real passwords.
(function () {
  const usersKey = "activity_buddy_users";
  const currentUserKey = "activity_buddy_current_user";
  const joinedGroupsKey = "activity_buddy_joined_groups";

  function loadUsers() {
    try {
      const savedUsers = JSON.parse(localStorage.getItem(usersKey) || "[]");
      if (Array.isArray(savedUsers)) {
        return savedUsers;
      }
    } catch (error) {
      return [];
    }
    return [];
  }

  function loadCurrentUser() {
    try {
      const user = JSON.parse(localStorage.getItem(currentUserKey) || "null");
      if (user && user.displayName && user.username) {
        return user;
      }
    } catch (error) {
      return null;
    }
    return null;
  }

  function saveCurrentUser(user) {
    localStorage.setItem(currentUserKey, JSON.stringify(user));
  }

  function loadJoinedGroups() {
    try {
      const joinedGroups = JSON.parse(localStorage.getItem(joinedGroupsKey) || "{}");
      if (joinedGroups && typeof joinedGroups === "object" && !Array.isArray(joinedGroups)) {
        return joinedGroups;
      }
    } catch (error) {
      return {};
    }
    return {};
  }

  function getJoinedGroupKeys(user) {
    if (!user) {
      return [];
    }
    const joinedGroups = loadJoinedGroups();
    const username = user.username.toLowerCase();
    return Array.isArray(joinedGroups[username]) ? joinedGroups[username] : [];
  }

  function rememberJoinedGroup(user, groupKey) {
    const joinedGroups = loadJoinedGroups();
    const username = user.username.toLowerCase();
    const userGroups = Array.isArray(joinedGroups[username]) ? joinedGroups[username] : [];
    if (userGroups.indexOf(groupKey) === -1) {
      userGroups.push(groupKey);
    }
    joinedGroups[username] = userGroups;
    localStorage.setItem(joinedGroupsKey, JSON.stringify(joinedGroups));
  }

  function forgetGroupForEveryone(groupKey) {
    const joinedGroups = loadJoinedGroups();
    Object.keys(joinedGroups).forEach(function (username) {
      if (!Array.isArray(joinedGroups[username])) {
        return;
      }
      joinedGroups[username] = joinedGroups[username].filter(function (savedKey) {
        return savedKey !== groupKey;
      });
    });
    localStorage.setItem(joinedGroupsKey, JSON.stringify(joinedGroups));
  }

  function makeGroupId(user) {
    return "group-" + user.username.toLowerCase() + "-" + Date.now().toString(36)
      + "-" + Math.random().toString(36).slice(2, 8);
  }

  function loadActivityGroups() {
    const dataElement = document.getElementById("activity-group-data");
    if (!dataElement) {
      return [];
    }
    try {
      const groups = JSON.parse(dataElement.textContent);
      return Array.isArray(groups) ? groups : [];
    } catch (error) {
      return [];
    }
  }

  function timesOverlap(newStart, newEnd, oldStart, oldEnd) {
    return newStart < oldEnd && newEnd > oldStart;
  }

  function findScheduleConflict(targetGroup, joinedKeys, allGroups) {
    if (!targetGroup.date || !targetGroup.start_time || !targetGroup.end_time) {
      return null;
    }
    for (let index = 0; index < allGroups.length; index += 1) {
      const oldGroup = allGroups[index];
      if (joinedKeys.indexOf(oldGroup.group_key) === -1) {
        continue;
      }
      if (!oldGroup.date || !oldGroup.start_time || !oldGroup.end_time) {
        continue;
      }
      if (targetGroup.date === oldGroup.date && timesOverlap(
        targetGroup.start_time,
        targetGroup.end_time,
        oldGroup.start_time,
        oldGroup.end_time
      )) {
        return oldGroup;
      }
    }
    return null;
  }

  function showJoinNotice(message) {
    const notice = document.querySelector("[data-demo-join-notice]");
    if (!notice) {
      return;
    }
    notice.textContent = message;
    notice.hidden = message === "";
    if (message !== "") {
      notice.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function findGroup(groupKey, allGroups) {
    return allGroups.find(function (group) {
      return group.group_key === groupKey;
    });
  }

  function updatePage3JoinButtons(user) {
    const allGroups = loadActivityGroups();
    const joinedKeys = getJoinedGroupKeys(user);

    document.querySelectorAll("[data-demo-group]").forEach(function (card) {
      const button = card.querySelector("[data-demo-join-button]");
      if (!button) {
        return;
      }

      const groupKey = card.dataset.groupKey;
      const isFull = card.dataset.isFull === "true";
      const targetGroup = findGroup(groupKey, allGroups);
      const conflict = user && targetGroup
        ? findScheduleConflict(targetGroup, joinedKeys, allGroups)
        : null;

      button.classList.remove("is-joined", "is-conflict", "is-full");
      if (user && joinedKeys.indexOf(groupKey) !== -1) {
        button.disabled = true;
        button.classList.add("is-joined");
        button.textContent = "✓ เข้าร่วมแล้ว";
      } else if (isFull) {
        button.disabled = true;
        button.classList.add("is-full");
        button.textContent = "เต็มแล้ว";
      } else if (conflict) {
        button.disabled = true;
        button.classList.add("is-conflict");
        button.textContent = "⚠ เวลาซ้อนกับกิจกรรมของคุณ";
      } else {
        button.disabled = false;
        button.textContent = "เข้าร่วมกลุ่ม";
      }
    });
  }

  function updateMyGroups(user) {
    const loginState = document.querySelector("[data-demo-my-groups-login]");
    const emptyState = document.querySelector("[data-demo-my-groups-empty]");
    const grid = document.querySelector("[data-demo-my-groups-grid]");
    if (!loginState || !emptyState || !grid) {
      return;
    }

    const joinedKeys = getJoinedGroupKeys(user);
    let visibleCount = 0;
    document.querySelectorAll("[data-demo-my-group-card]").forEach(function (card) {
      const isJoined = Boolean(user) && joinedKeys.indexOf(card.dataset.groupKey) !== -1;
      card.hidden = !isJoined;
      if (isJoined) {
        visibleCount += 1;
      }
    });

    loginState.hidden = Boolean(user);
    emptyState.hidden = !user || visibleCount > 0;
    grid.hidden = !user || visibleCount === 0;
  }

  function updateOwnerControls(user) {
    document.querySelectorAll("[data-demo-group]").forEach(function (card) {
      const controls = card.querySelector("[data-demo-owner-actions]");
      const editForm = card.querySelector("[data-demo-edit-form]");
      if (!controls) {
        return;
      }
      const ownerUsername = card.dataset.ownerUsername.toLowerCase();
      const isOwner = Boolean(user) && ownerUsername !== ""
        && ownerUsername === user.username.toLowerCase();
      controls.hidden = !isOwner;
      if (!isOwner && editForm) {
        editForm.hidden = true;
      }
    });
  }

  function showError(element, message) {
    if (!element) {
      return;
    }
    element.textContent = message;
    element.hidden = message === "";
  }

  function updateCreatorField(user) {
    const creatorInput = document.getElementById("creator");
    if (!creatorInput) {
      return;
    }

    if (user) {
      creatorInput.value = user.displayName;
      creatorInput.readOnly = true;
    } else {
      creatorInput.readOnly = false;
    }
  }

  function updateAccountDisplay() {
    const currentUser = loadCurrentUser();

    document.querySelectorAll("[data-demo-auth-profile]").forEach(function (profile) {
      profile.hidden = !currentUser;
      if (!currentUser) {
        return;
      }
      profile.querySelector("[data-demo-auth-display-name]").textContent = currentUser.displayName;
      profile.querySelector("[data-demo-auth-username]").textContent = currentUser.username;
    });

    document.querySelectorAll("[data-demo-auth-logged-out]").forEach(function (loggedOutArea) {
      loggedOutArea.hidden = Boolean(currentUser);
    });

    document.querySelectorAll("[data-demo-auth-greeting]").forEach(function (greeting) {
      greeting.hidden = !currentUser;
      greeting.textContent = currentUser
        ? "ยินดีต้อนรับกลับมา, " + currentUser.displayName + " 👋"
        : "";
    });

    updateCreatorField(currentUser);
    updatePage3JoinButtons(currentUser);
    updateMyGroups(currentUser);
    updateOwnerControls(currentUser);
  }

  const modal = document.querySelector("[data-demo-auth-modal]");
  const loginView = document.querySelector("[data-demo-auth-login-view]");
  const registerView = document.querySelector("[data-demo-auth-register-view]");
  const loginForm = document.querySelector("[data-demo-auth-login-form]");
  const registerForm = document.querySelector("[data-demo-auth-register-form]");
  const loginError = document.querySelector("[data-demo-auth-login-error]");
  const registerError = document.querySelector("[data-demo-auth-register-error]");

  function showLoginView() {
    if (!modal) {
      return;
    }
    modal.hidden = false;
    loginView.hidden = false;
    registerView.hidden = true;
    showError(loginError, "");
    document.getElementById("demo-login-username").focus();
  }

  function showRegisterView() {
    loginView.hidden = true;
    registerView.hidden = false;
    showError(registerError, "");
    document.getElementById("demo-register-display-name").focus();
  }

  function closeModal() {
    if (modal) {
      modal.hidden = true;
    }
  }

  document.querySelectorAll("[data-demo-auth-open]").forEach(function (button) {
    button.addEventListener("click", showLoginView);
  });

  document.querySelectorAll("[data-demo-auth-close]").forEach(function (button) {
    button.addEventListener("click", closeModal);
  });

  const showRegisterButton = document.querySelector("[data-demo-auth-show-register]");
  if (showRegisterButton) {
    showRegisterButton.addEventListener("click", showRegisterView);
  }

  const showLoginButton = document.querySelector("[data-demo-auth-show-login]");
  if (showLoginButton) {
    showLoginButton.addEventListener("click", showLoginView);
  }

  if (modal) {
    modal.addEventListener("click", function (event) {
      if (event.target === modal) {
        closeModal();
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", function (event) {
      event.preventDefault();

      const displayName = document.getElementById("demo-register-display-name").value.trim();
      const username = document.getElementById("demo-register-username").value.trim();
      const password = document.getElementById("demo-register-password").value;
      const confirmation = document.getElementById("demo-register-confirmation").value;

      if (displayName === "") {
        showError(registerError, "กรุณากรอกชื่อที่แสดง");
        return;
      }
      if (username === "") {
        showError(registerError, "กรุณากรอกชื่อผู้ใช้");
        return;
      }
      if (password.length < 4) {
        showError(registerError, "รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร");
        return;
      }
      if (password !== confirmation) {
        showError(registerError, "รหัสผ่านไม่ตรงกัน");
        return;
      }

      const users = loadUsers();
      const duplicateUser = users.find(function (user) {
        return user.username.toLowerCase() === username.toLowerCase();
      });
      if (duplicateUser) {
        showError(registerError, "ชื่อผู้ใช้นี้ถูกใช้แล้ว");
        return;
      }

      users.push({
        displayName: displayName,
        username: username,
        password: password
      });
      localStorage.setItem(usersKey, JSON.stringify(users));
      saveCurrentUser({ displayName: displayName, username: username });
      registerForm.reset();
      closeModal();
      updateAccountDisplay();
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", function (event) {
      event.preventDefault();

      const username = document.getElementById("demo-login-username").value.trim();
      const password = document.getElementById("demo-login-password").value;
      const users = loadUsers();
      const matchingUser = users.find(function (user) {
        return user.username.toLowerCase() === username.toLowerCase()
          && user.password === password;
      });

      if (!matchingUser) {
        showError(loginError, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง");
        return;
      }

      saveCurrentUser({
        displayName: matchingUser.displayName,
        username: matchingUser.username
      });
      loginForm.reset();
      closeModal();
      updateAccountDisplay();
    });
  }

  const createGroupForm = document.querySelector("[data-demo-create-form]");
  if (createGroupForm) {
    createGroupForm.addEventListener("submit", function (event) {
      const currentUser = loadCurrentUser();
      if (!currentUser) {
        return;
      }
      event.preventDefault();

      const groupId = makeGroupId(currentUser);
      createGroupForm.querySelector("[name='creator_username']").value = currentUser.username;
      createGroupForm.querySelector("[name='group_id']").value = groupId;

      const submitButton = createGroupForm.querySelector("[type='submit']");
      submitButton.disabled = true;
      submitButton.textContent = "กำลังสร้างกลุ่ม...";

      const createUrl = createGroupForm.getAttribute("action");
      fetch(createUrl, {
        method: "POST",
        body: new FormData(createGroupForm),
        credentials: "same-origin"
      }).then(function (response) {
        const responseUrl = new URL(response.url);
        const message = responseUrl.searchParams.get("msg") || "";
        if (message.indexOf("✓") === 0) {
          rememberJoinedGroup(currentUser, groupId);
        }
        window.location.href = response.url;
      }).catch(function () {
        submitButton.disabled = false;
        submitButton.textContent = "สร้างกลุ่มกิจกรรม";
        showJoinNotice("ไม่สามารถสร้างกลุ่มได้ กรุณาลองอีกครั้ง");
      });
    });
  }

  document.querySelectorAll("[data-demo-edit-open]").forEach(function (button) {
    button.addEventListener("click", function () {
      const card = button.closest("[data-demo-group]");
      const editForm = card.querySelector("[data-demo-edit-form]");
      editForm.hidden = false;
      editForm.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });

  document.querySelectorAll("[data-demo-edit-cancel]").forEach(function (button) {
    button.addEventListener("click", function () {
      const editForm = button.closest("[data-demo-edit-form]");
      editForm.reset();
      editForm.hidden = true;
    });
  });

  document.querySelectorAll("[data-demo-edit-form]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      const currentUser = loadCurrentUser();
      if (!currentUser) {
        event.preventDefault();
        showJoinNotice("กรุณาเข้าสู่ระบบก่อนแก้ไขกลุ่ม");
        return;
      }
      form.querySelector("[name='username']").value = currentUser.username;
      form.querySelector("[name='joined_group_keys']").value = JSON.stringify(
        getJoinedGroupKeys(currentUser)
      );
    });
  });

  const deleteModal = document.querySelector("[data-demo-delete-modal]");
  const deleteForm = document.querySelector("[data-demo-delete-form]");

  function closeDeleteModal() {
    if (deleteModal) {
      deleteModal.hidden = true;
    }
  }

  document.querySelectorAll("[data-demo-delete-open]").forEach(function (button) {
    button.addEventListener("click", function () {
      const currentUser = loadCurrentUser();
      if (!currentUser || !deleteModal || !deleteForm) {
        showJoinNotice("กรุณาเข้าสู่ระบบก่อนลบกลุ่ม");
        return;
      }
      deleteForm.querySelector("[name='group_index']").value = button.dataset.groupIndex;
      deleteForm.querySelector("[name='username']").value = currentUser.username;
      deleteForm.querySelector("[name='deleted_group_key']").value = button.dataset.groupKey;
      deleteModal.hidden = false;
    });
  });

  document.querySelectorAll("[data-demo-delete-cancel]").forEach(function (button) {
    button.addEventListener("click", closeDeleteModal);
  });

  if (deleteModal) {
    deleteModal.addEventListener("click", function (event) {
      if (event.target === deleteModal) {
        closeDeleteModal();
      }
    });
  }

  if (deleteForm) {
    deleteForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const currentUser = loadCurrentUser();
      if (!currentUser) {
        closeDeleteModal();
        showJoinNotice("กรุณาเข้าสู่ระบบก่อนลบกลุ่ม");
        return;
      }

      deleteForm.querySelector("[name='username']").value = currentUser.username;
      const deletedGroupKey = deleteForm.querySelector("[name='deleted_group_key']").value;
      const deleteUrl = deleteForm.getAttribute("action");
      fetch(deleteUrl, {
        method: "POST",
        body: new FormData(deleteForm),
        credentials: "same-origin"
      }).then(function (response) {
        const responseUrl = new URL(response.url);
        const message = responseUrl.searchParams.get("msg") || "";
        if (message.indexOf("✓") === 0) {
          forgetGroupForEveryone(deletedGroupKey);
        }
        window.location.href = response.url;
      }).catch(function () {
        closeDeleteModal();
        showJoinNotice("ไม่สามารถลบกลุ่มได้ กรุณาลองอีกครั้ง");
      });
    });
  }

  document.querySelectorAll("[data-demo-join-form]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();

      const currentUser = loadCurrentUser();
      if (!currentUser) {
        showJoinNotice("กรุณาเข้าสู่ระบบก่อนเข้าร่วมกลุ่ม");
        return;
      }

      const card = form.closest("[data-demo-group]");
      const groupKey = card.dataset.groupKey;
      const allGroups = loadActivityGroups();
      const joinedKeys = getJoinedGroupKeys(currentUser);
      const targetGroup = findGroup(groupKey, allGroups);

      if (joinedKeys.indexOf(groupKey) !== -1) {
        showJoinNotice("✓ คุณเข้าร่วมกลุ่มนี้แล้ว");
        updatePage3JoinButtons(currentUser);
        return;
      }
      if (card.dataset.isFull === "true") {
        showJoinNotice("กลุ่มกิจกรรมนี้เต็มแล้ว");
        return;
      }

      const conflict = targetGroup
        ? findScheduleConflict(targetGroup, joinedKeys, allGroups)
        : null;
      if (conflict) {
        showJoinNotice(
          "⚠ ตารางกิจกรรมซ้อนกัน: " + conflict.activity + " "
          + conflict.start_time + "–" + conflict.end_time
        );
        updatePage3JoinButtons(currentUser);
        return;
      }

      form.querySelector("[name='username']").value = currentUser.username;
      form.querySelector("[name='joined_group_keys']").value = JSON.stringify(joinedKeys);

      const button = form.querySelector("[data-demo-join-button]");
      button.disabled = true;
      button.textContent = "กำลังเข้าร่วม...";

      const joinUrl = form.getAttribute("action");
      fetch(joinUrl, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin"
      }).then(function (response) {
        const responseUrl = new URL(response.url);
        const message = responseUrl.searchParams.get("msg") || "";
        if (message.indexOf("✓") === 0) {
          rememberJoinedGroup(currentUser, groupKey);
          window.location.href = response.url;
          return;
        }
        showJoinNotice(message || "ไม่สามารถเข้าร่วมกลุ่มได้ กรุณาลองอีกครั้ง");
        updatePage3JoinButtons(currentUser);
      }).catch(function () {
        showJoinNotice("ไม่สามารถเข้าร่วมกลุ่มได้ กรุณาลองอีกครั้ง");
        updatePage3JoinButtons(currentUser);
      });
    });
  });

  document.querySelectorAll("[data-demo-auth-logout]").forEach(function (button) {
    button.addEventListener("click", function () {
      localStorage.removeItem(currentUserKey);
      if (window.location.pathname !== "/") {
        window.location.href = "/";
        return;
      }
      updateAccountDisplay();
    });
  });

  updateAccountDisplay();
}());
