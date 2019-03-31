import sys
from . import environments as env



def apply():
    sys.modules['instapy'].InstaPy.like_by_locations.__code__ = like_by_locations_patch.__code__
    sys.modules['instapy'].InstaPy.unfollow_users.__code__ = unfollow_users.__code__
    sys.modules['instapy.unfollow_util'].unfollow_user.__code__ = unfollow_user_patch.__code__
    sys.modules['instapy.unfollow_util'].follow_user.__code__ = follow_user_patch.__code__

def unfollow_users(self,
                   amount=10,
                   customList=(False, [], "all"),
                   InstapyFollowed=(False, "all"),
                   nonFollowers=False,
                   allFollowing=False,
                   style="FIFO",
                   unfollow_after=None,
                   delay_followbackers=0,  # 864000 = 10 days, 0 = don't delay
                   sleep_delay=600):
    """Unfollows (default) 10 users from your following list"""

    if self.aborting:
        return self

    message = "Starting to unfollow users.."
    highlight_print(self.username, message,
                    "feature", "info", self.logger)

    if unfollow_after is not None:
        if not python_version().startswith(('2.7', '3')):
            self.logger.warning(
                "`unfollow_after` parameter is not"
                " available for Python versions below 2.7")
            unfollow_after = None

    self.automatedFollowedPool = set_automated_followed_pool(
        self.username,
        unfollow_after,
        self.logger,
        self.logfolder,
        delay_followbackers)

    try:
        unfollowed = unfollow(self.browser,
                              self.username,
                              amount,
                              customList,
                              InstapyFollowed,
                              nonFollowers,
                              allFollowing,
                              style,
                              self.automatedFollowedPool,
                              self.relationship_data,
                              self.dont_include,
                              self.white_list,
                              sleep_delay,
                              self.jumps,
                              delay_followbackers,
                              self.logger,
                              self.logfolder)
        self.logger.info(
            "--> Total people unfollowed : {}\n".format(unfollowed))
        self.unfollowed += unfollowed

    except Exception as exc:
        if isinstance(exc, RuntimeWarning):
            self.logger.warning(
                u'Warning: {} , stopping unfollow_users'.format(exc))
            return self

        else:
            self.logger.error('Sorry, an error occurred: {}'.format(exc))
            return self

    return self


def follow_user_patch(browser, track, login, user_name, button, blacklist, logger,
                logfolder):
    """ Follow a user either from the profile page or post page or dialog
    box """
    # list of available tracks to follow in: ["profile", "post" "dialog"]

    # check action availability
    if quota_supervisor("follows") == "jump":
        return False, "jumped"

    if track in ["profile", "post"]:
        if track == "profile":
            # check URL of the webpage, if it already is user's profile
            # page, then do not navigate to it again
            user_link = "https://www.instagram.com/{}/".format(user_name)
            web_address_navigator(browser, user_link)

        # find out CURRENT following status
        following_status, follow_button = get_following_status(browser,
                                                               track,
                                                               login,
                                                               user_name,
                                                               None,
                                                               logger,
                                                               logfolder)
        if following_status in ["Follow", "Follow Back"]:
            click_visibly(browser, follow_button)  # click to follow
            follow_state, msg = verify_action(browser, "follow", track, login,
                                              user_name, None, logger,
                                              logfolder)
            if follow_state is not True:
                logger.warning("!!!!!Retrying!!!!!!!")
                return follow_user_patch(browser, track, login, user_name, button, blacklist, logger,logfolder)

        elif following_status in ["Following", "Requested"]:
            if following_status == "Following":
                logger.info("--> Already following '{}'!\n".format(user_name))

            elif following_status == "Requested":
                logger.info("--> Already requested '{}' to follow!\n".format(
                    user_name))

            sleep(1)
            return False, "already followed"

        elif following_status in ["Unblock", "UNAVAILABLE"]:
            if following_status == "Unblock":
                failure_msg = "user is in block"

            elif following_status == "UNAVAILABLE":
                failure_msg = "user is inaccessible"

            logger.warning(
                "--> Couldn't follow '{}'!\t~{}".format(user_name,
                                                        failure_msg))
            return False, following_status

        elif following_status is None:
            sirens_wailing, emergency_state = emergency_exit(browser, login,
                                                             logger)
            if sirens_wailing is True:
                return False, emergency_state

            else:
                logger.warning(
                    "--> Couldn't unfollow '{}'!\t~unexpected failure".format(
                        user_name))
                return False, "unexpected failure"
    elif track == "dialog":
        click_element(browser, button)
        sleep(3)

    # general tasks after a successful follow
    logger.info("--> Followed '{}'!".format(user_name.encode("utf-8")))
    update_activity('follows')

    # get user ID to record alongside username
    user_id = get_user_id(browser, track, user_name, logger)

    logtime = datetime.now().strftime('%Y-%m-%d %H:%M')
    log_followed_pool(login, user_name, logger, logfolder, logtime, user_id)

    follow_restriction("write", user_name, None, logger)

    if blacklist['enabled'] is True:
        action = 'followed'
        add_user_to_blacklist(user_name,
                              blacklist['campaign'],
                              action,
                              logger,
                              logfolder)

    # get the post-follow delay time to sleep
    naply = get_action_delay("follow")
    sleep(naply)

    return True, "success"
    
    
    
def unfollow_user_patch(browser, track, username, person, person_id, button,
                  relationship_data, logger, logfolder):
    """ Unfollow a user either from the profile or post page or dialog box """
    # list of available tracks to unfollow in: ["profile", "post" "dialog"]

    # check action availability
    if quota_supervisor("unfollows") == "jump":
        return False, "jumped"

    if track in ["profile", "post"]:
        """ Method of unfollowing from a user's profile page or post page """
        if track == "profile":
            user_link = "https://www.instagram.com/{}/".format(person)
            web_address_navigator(browser, user_link)

        # find out CURRENT follow status
        following_status, follow_button = get_following_status(browser,
                                                               track,
                                                               username,
                                                               person,
                                                               person_id,
                                                               logger,
                                                               logfolder)

        if following_status in ["Following", "Requested"]:
            click_element(browser, follow_button)  # click to unfollow
            sleep(4)  # TODO: use explicit wait here
            confirm_unfollow(browser)
            unfollow_state, msg = verify_action(browser, "unfollow", track,
                                                username,
                                                person, person_id, logger,
                                                logfolder)
            if unfollow_state is not True:
                logger.warning("!!!!!!!!!!!!!!!!!!!!retrying!")
                return unfollow_user_patch(browser, track, username, person, person_id, button,
                  relationship_data, logger, logfolder)

        elif following_status in ["Follow", "Follow Back"]:
            logger.info(
                "--> Already unfollowed '{}'! or a private user that "
                "rejected your req".format(
                    person))
            post_unfollow_cleanup(["successful", "uncertain"], username,
                                  person, relationship_data, person_id, logger,
                                  logfolder)
            return False, "already unfollowed"

        elif following_status in ["Unblock", "UNAVAILABLE"]:
            if following_status == "Unblock":
                failure_msg = "user is in block"

            elif following_status == "UNAVAILABLE":
                failure_msg = "user is inaccessible"

            logger.warning(
                "--> Couldn't unfollow '{}'!\t~{}".format(person, failure_msg))
            post_unfollow_cleanup("uncertain", username, person,
                                  relationship_data, person_id, logger,
                                  logfolder)
            return False, following_status

        elif following_status is None:
            sirens_wailing, emergency_state = emergency_exit(browser, username,
                                                             logger)
            if sirens_wailing is True:
                return False, emergency_state

            else:
                logger.warning(
                    "--> Couldn't unfollow '{}'!\t~unexpected failure".format(
                        person))
                return False, "unexpected failure"
    elif track == "dialog":
        """  Method of unfollowing from a dialog box """
        click_element(browser, button)
        sleep(4)  # TODO: use explicit wait here
        confirm_unfollow(browser)

    # general tasks after a successful unfollow
    logger.info("--> Unfollowed '{}'!".format(person))
    update_activity('unfollows')
    post_unfollow_cleanup("successful", username, person, relationship_data,
                          person_id, logger, logfolder)

    # get the post-unfollow delay time to sleep
    naply = get_action_delay("unfollow")
    sleep(naply)

    return True, "success"
    
    

def like_by_locations_patch(self,
                      locations=None,
                      amount=50,
                      media=None,
                      skip_top_posts=True):
    """Likes (default) 50 images per given locations"""
    if self.aborting:
        return self

    liked_img = 0
    already_liked = 0
    inap_img = 0
    commented = 0
    followed = 0
    not_valid_users = 0

    locations = locations or []
    self.quotient_breach = False

    for index, location in enumerate(locations):
        if self.quotient_breach:
            break

        self.logger.info('Location [{}/{}]'
                         .format(index + 1, len(locations)))
        self.logger.info('--> {}'.format(location.encode('utf-8')))

        try:
            links2 = get_links_for_location(self.browser,
                                           location,
                                           50,
                                           self.logger,
                                           media,
                                           skip_top_posts)
            random.shuffle(links2)
            links = links2[:1]
        except NoSuchElementException as exc:
            self.logger.warning(
                "Error occurred while getting images from location: {}  "
                "~maybe too few images exist\n\t{}\n".format(location, str(
                    exc).encode("utf-8")))
            continue

        for i, link in enumerate(links):
            if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
                "likes"]:
                self.logger.warning(
                    "--> Like quotient reached its peak!\t~leaving "
                    "Like-By-Locations activity\n")
                self.quotient_breach = True
                # reset jump counter after a breach report
                self.jumps["consequent"]["likes"] = 0
                break

            self.logger.info('[{}/{}]'.format(i + 1, len(links)))
            self.logger.info(link)

            try:
                inappropriate, user_name, is_video, reason, scope = (
                    check_link(self.browser,
                               link,
                               self.dont_like,
                               self.mandatory_words,
                               self.mandatory_language,
                               self.is_mandatory_character,
                               self.mandatory_character,
                               self.check_character_set,
                               self.ignore_if_contains,
                               self.logger))

                if not inappropriate and self.delimit_liking:
                    self.liking_approved = verify_liking(self.browser,
                                                         self.max_likes,
                                                         self.min_likes,
                                                         self.logger)

                if not inappropriate and self.liking_approved:
                    # validate user
                    validation, details = self.validate_user_call(
                        user_name)

                    if validation is not True:
                        self.logger.info(
                            "--> Not a valid user: {}".format(details))
                        not_valid_users += 1
                        continue
                    else:
                        web_address_navigator(self.browser, link)

                    # try to like
                    like_state, msg = like_image(self.browser,
                                                 user_name,
                                                 self.blacklist,
                                                 self.logger,
                                                 self.logfolder)

                    if like_state is True:
                        liked_img += 1
                        # reset jump counter after a successful like
                        self.jumps["consequent"]["likes"] = 0

                        checked_img = True
                        temp_comments = []

                        commenting = random.randint(
                            0, 100) <= self.comment_percentage
                        following = random.randint(
                            0, 100) <= self.follow_percentage

                        if self.use_clarifai and (following or commenting):
                            try:
                                checked_img, temp_comments, \
                                clarifai_tags = (
                                    self.query_clarifai())

                            except Exception as err:
                                self.logger.error(
                                    'Image check error: {}'.format(err))

                        # comments
                        if (self.do_comment and
                                user_name not in self.dont_include and
                                checked_img and
                                commenting):

                            if self.delimit_commenting:
                                (self.commenting_approved,
                                 disapproval_reason) = verify_commenting(
                                    self.browser,
                                    self.max_comments,
                                    self.min_comments,
                                    self.comments_mandatory_words,
                                    self.logger)
                            if self.commenting_approved:
                                # smart commenting
                                comments = self.fetch_smart_comments(
                                    is_video,
                                    temp_comments)
                                if comments:
                                    comment_state, msg = comment_image(
                                        self.browser,
                                        user_name,
                                        comments,
                                        self.blacklist,
                                        self.logger,
                                        self.logfolder)
                                    if comment_state is True:
                                        commented += 1

                            else:
                                self.logger.info(disapproval_reason)

                        else:
                            self.logger.info('--> Not commented')
                            sleep(1)

                        # following
                        if (self.do_follow and
                                user_name not in self.dont_include and
                                checked_img and
                                following and
                                not follow_restriction("read", user_name,
                                                       self.follow_times,
                                                       self.logger)):

                            follow_state, msg = follow_user(self.browser,
                                                            "post",
                                                            self.username,
                                                            user_name,
                                                            None,
                                                            self.blacklist,
                                                            self.logger,
                                                            self.logfolder)
                            if follow_state is True:
                                followed += 1

                        else:
                            self.logger.info('--> Not following')
                            sleep(1)

                    elif msg == "already liked":
                        already_liked += 1

                    elif msg == "jumped":
                        # will break the loop after certain consecutive
                        # jumps
                        self.jumps["consequent"]["likes"] += 1

                else:
                    self.logger.info(
                        '--> Image not liked: {}'.format(
                            reason.encode('utf-8')))
                    inap_img += 1

            except NoSuchElementException as err:
                self.logger.error('Invalid Page: {}'.format(err))

        self.logger.info('Location: {}'.format(location.encode('utf-8')))
        self.logger.info('Liked: {}'.format(liked_img))
        self.logger.info('Already Liked: {}'.format(already_liked))
        self.logger.info('Commented: {}'.format(commented))
        self.logger.info('Followed: {}'.format(followed))
        self.logger.info('Inappropriate: {}'.format(inap_img))
        self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    self.followed += followed
    self.liked_img += liked_img
    self.already_liked += already_liked
    self.commented += commented
    self.inap_img += inap_img
    self.not_valid_users += not_valid_users

    return self